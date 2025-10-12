"""
Orquestrador Principal do Proxygenesis AI
Implementa o loop completo de coleta, validação e aprendizado
"""

import asyncio
import logging
import os
import csv
import time
from datetime import datetime
from typing import List, Dict
import pandas as pd

from scraper import ProxyScraper
from checker import ProxyChecker
from trainer import ProxyTrainer
from hybrid_collector import HybridCollector
from settings import MAIN_LOOP_CONFIG, PATHS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('proxygenesis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProxygenesisAI:
    def __init__(self, shodan_api_key: str = None):
        self.scraper = ProxyScraper()
        self.checker = ProxyChecker()
        self.trainer = ProxyTrainer()
        self.hybrid_collector = HybridCollector(shodan_api_key)
        self.cycle_count = 0
        self.total_proxies_found = 0
        self.total_proxies_validated = 0
        self.total_active_proxies = 0
        
        # Criar diretórios se não existirem
        os.makedirs(PATHS['data_dir'], exist_ok=True)
        os.makedirs(PATHS['models_dir'], exist_ok=True)
        
        # Carregar modelo existente se disponível
        self._load_existing_model()
    
    def _load_existing_model(self):
        """Carrega modelo existente se disponível"""
        if os.path.exists(PATHS['model_file']):
            if self.trainer.load_model():
                logger.info("Modelo existente carregado com sucesso")
            else:
                logger.warning("Falha ao carregar modelo existente")
        else:
            logger.info("Nenhum modelo existente encontrado")
    
    async def run_cycle(self) -> Dict:
        """
        Executa um ciclo completo do sistema
        
        Returns:
            Dicionário com estatísticas do ciclo
        """
        self.cycle_count += 1
        logger.info(f"=== INICIANDO CICLO {self.cycle_count} ===")
        
        cycle_start_time = time.time()
        cycle_stats = {
            'cycle': self.cycle_count,
            'start_time': datetime.now().isoformat(),
            'candidates_collected': 0,
            'candidates_tested': 0,
            'active_proxies_found': 0,
            'model_retrained': False,
            'duration_seconds': 0
        }
        
        try:
            # Fase 1: Coleta Híbrida de Proxies Candidatos
            logger.info("Fase 1: Coletando proxies candidatos (método híbrido)...")
            candidates_data = await self.hybrid_collector.run_hybrid_collection()
            cycle_stats['candidates_collected'] = len(candidates_data)
            
            if not candidates_data:
                logger.warning("Nenhum proxy candidato encontrado neste ciclo")
                return cycle_stats
            
            # Extrair apenas os proxies para validação
            candidates = [candidate['proxy'] for candidate in candidates_data]
            
            # Fase 2: Priorização Inteligente (se modelo disponível)
            if self.trainer.is_trained:
                logger.info("Fase 2: Priorizando candidatos com ML...")
                candidates_data = await self._prioritize_candidates_with_ml(candidates_data)
                candidates = [candidate['proxy'] for candidate in candidates_data]
            
            # Fase 3: Validação de Proxies
            logger.info("Fase 3: Validando proxies...")
            validation_results = await self.checker.validate_proxies(candidates)
            cycle_stats['candidates_tested'] = len(validation_results)
            
            # Filtrar proxies ativos
            active_proxies = [r for r in validation_results if r['is_active']]
            cycle_stats['active_proxies_found'] = len(active_proxies)
            
            # Atualizar contadores globais
            self.total_proxies_found += len(candidates)
            self.total_proxies_validated += len(validation_results)
            self.total_active_proxies += len(active_proxies)
            
            # Salvar proxies ativos
            if active_proxies:
                await self._save_active_proxies(active_proxies)
            
            # Fase 4: Atualizar Dados de Treinamento
            logger.info("Fase 4: Atualizando dados de treinamento...")
            await self._update_training_data(validation_results, candidates_data)
            
            # Fase 5: Retreinar Modelo (se necessário)
            if self._should_retrain():
                logger.info("Fase 5: Retreinando modelo...")
                await self._retrain_model()
                cycle_stats['model_retrained'] = True
            
            # Calcular estatísticas finais
            cycle_stats['duration_seconds'] = time.time() - cycle_start_time
            cycle_stats['success_rate'] = (len(active_proxies) / len(validation_results) * 100) if validation_results else 0
            
            logger.info(f"Ciclo {self.cycle_count} concluído em {cycle_stats['duration_seconds']:.1f}s")
            logger.info(f"Proxies ativos encontrados: {len(active_proxies)}")
            logger.info(f"Taxa de sucesso: {cycle_stats['success_rate']:.1f}%")
            
        except Exception as e:
            logger.error(f"Erro no ciclo {self.cycle_count}: {e}")
            cycle_stats['error'] = str(e)
        
        return cycle_stats
    
    async def _prioritize_candidates_with_ml(self, candidates_data: List[Dict]) -> List[Dict]:
        """
        Prioriza candidatos usando o modelo de ML com dados completos
        
        Args:
            candidates_data: Lista de dados de candidatos com metadados
            
        Returns:
            Lista priorizada de candidatos
        """
        try:
            # Obter probabilidades usando o modelo
            probabilities = self.trainer.predict_proxy_probability(candidates_data)
            
            # Combinar dados com probabilidades
            for i, candidate in enumerate(candidates_data):
                candidate['ml_probability'] = probabilities[i]
            
            # Ordenar por probabilidade ML + qualidade da fonte
            def priority_score(candidate):
                ml_prob = candidate.get('ml_probability', 0.5)
                quality_score = candidate.get('quality_score', 0.5)
                # Combinar probabilidade ML (70%) com qualidade da fonte (30%)
                return ml_prob * 0.7 + quality_score * 0.3
            
            candidates_data.sort(key=priority_score, reverse=True)
            
            # Limitar número de candidatos
            top_count = min(MAIN_LOOP_CONFIG['top_candidates_to_test'], len(candidates_data))
            prioritized = candidates_data[:top_count]
            
            logger.info(f"Priorizados {len(prioritized)} candidatos de {len(candidates_data)}")
            
            # Mostrar top 5
            if prioritized:
                logger.info("Top 5 candidatos priorizados:")
                for i, candidate in enumerate(prioritized[:5], 1):
                    logger.info(f"  {i}. {candidate['proxy']} "
                              f"(ML: {candidate.get('ml_probability', 0):.3f}, "
                              f"Qualidade: {candidate.get('quality_score', 0):.3f}, "
                              f"Fonte: {candidate.get('source', 'unknown')})")
            
            return prioritized
            
        except Exception as e:
            logger.error(f"Erro na priorização com ML: {e}")
            return candidates_data[:MAIN_LOOP_CONFIG['top_candidates_to_test']]
    
    async def _save_active_proxies(self, active_proxies: List[Dict]):
        """Salva proxies ativos em arquivo"""
        try:
            with open(PATHS['active_proxies'], 'a', encoding='utf-8') as f:
                for proxy_data in active_proxies:
                    f.write(f"{proxy_data['proxy']}\n")
            
            logger.info(f"Salvos {len(active_proxies)} proxies ativos")
        except Exception as e:
            logger.error(f"Erro ao salvar proxies ativos: {e}")
    
    async def _update_training_data(self, validation_results: List[Dict], candidates_data: List[Dict] = None):
        """Atualiza dados de treinamento com novos resultados"""
        try:
            # Adicionar timestamp aos dados
            for result in validation_results:
                result['timestamp'] = datetime.now().isoformat()
            
            # Se temos dados de candidatos, adicionar metadados
            if candidates_data:
                # Criar mapeamento de proxy para metadados
                proxy_metadata = {candidate['proxy']: candidate for candidate in candidates_data}
                
                # Adicionar metadados aos resultados de validação
                for result in validation_results:
                    proxy = result['proxy']
                    if proxy in proxy_metadata:
                        metadata = proxy_metadata[proxy]
                        result.update({
                            'source': metadata.get('source', 'unknown'),
                            'discovery_method': metadata.get('discovery_method', 'unknown'),
                            'quality_score': metadata.get('quality_score', 0.5)
                        })
            
            # Carregar dados existentes
            existing_data = []
            if os.path.exists(PATHS['training_data']):
                df = pd.read_csv(PATHS['training_data'])
                existing_data = df.to_dict('records')
            
            # Adicionar novos dados
            all_data = existing_data + validation_results
            
            # Salvar dados atualizados
            df = pd.DataFrame(all_data)
            df.to_csv(PATHS['training_data'], index=False)
            
            logger.info(f"Dados de treinamento atualizados: {len(all_data)} registros")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar dados de treinamento: {e}")
    
    def _should_retrain(self) -> bool:
        """Verifica se o modelo deve ser retreinado"""
        if not self.trainer.is_trained:
            return True
        
        return (self.cycle_count % MAIN_LOOP_CONFIG['retrain_frequency'] == 0)
    
    async def _retrain_model(self):
        """Retreina o modelo com dados atualizados"""
        try:
            if not os.path.exists(PATHS['training_data']):
                logger.warning("Nenhum dado de treinamento disponível")
                return
            
            # Carregar dados
            df = pd.read_csv(PATHS['training_data'])
            
            if len(df) < MAIN_LOOP_CONFIG['min_training_samples']:
                logger.warning(f"Dados insuficientes para retreinamento: {len(df)}")
                return
            
            # Treinar modelo
            metrics = self.trainer.train_model(df)
            
            if 'error' not in metrics:
                # Salvar modelo
                self.trainer.save_model()
                logger.info(f"Modelo retreinado com sucesso. Acurácia: {metrics['accuracy']:.3f}")
            else:
                logger.error(f"Erro no retreinamento: {metrics['error']}")
                
        except Exception as e:
            logger.error(f"Erro no retreinamento: {e}")
    
    def get_system_stats(self) -> Dict:
        """Retorna estatísticas gerais do sistema"""
        return {
            'cycles_completed': self.cycle_count,
            'total_candidates_collected': self.total_proxies_found,
            'total_candidates_validated': self.total_proxies_validated,
            'total_active_proxies': self.total_active_proxies,
            'overall_success_rate': (self.total_active_proxies / self.total_proxies_validated * 100) if self.total_proxies_validated > 0 else 0,
            'model_trained': self.trainer.is_trained,
            'active_proxies_file': PATHS['active_proxies'],
            'training_data_file': PATHS['training_data']
        }
    
    async def run_continuous(self, max_cycles: int = None):
        """
        Executa o sistema continuamente
        
        Args:
            max_cycles: Número máximo de ciclos (None para infinito)
        """
        logger.info("Iniciando execução contínua do Proxygenesis AI")
        
        try:
            cycle = 0
            while max_cycles is None or cycle < max_cycles:
                cycle += 1
                
                # Executar ciclo
                cycle_stats = await self.run_cycle()
                
                # Mostrar estatísticas
                self._print_cycle_stats(cycle_stats)
                
                # Pausa entre ciclos
                if max_cycles is None or cycle < max_cycles:
                    logger.info("Aguardando próximo ciclo...")
                    await asyncio.sleep(60)  # 1 minuto entre ciclos
                
        except KeyboardInterrupt:
            logger.info("Execução interrompida pelo usuário")
        except Exception as e:
            logger.error(f"Erro na execução contínua: {e}")
        finally:
            # Mostrar estatísticas finais
            final_stats = self.get_system_stats()
            self._print_final_stats(final_stats)
    
    def _print_cycle_stats(self, stats: Dict):
        """Imprime estatísticas do ciclo"""
        print(f"\n=== CICLO {stats['cycle']} CONCLUÍDO ===")
        print(f"Duração: {stats['duration_seconds']:.1f}s")
        print(f"Candidatos coletados: {stats['candidates_collected']}")
        print(f"Candidatos testados: {stats['candidates_tested']}")
        print(f"Proxies ativos encontrados: {stats['active_proxies_found']}")
        print(f"Taxa de sucesso: {stats.get('success_rate', 0):.1f}%")
        if stats.get('model_retrained'):
            print("Modelo retreinado ✓")
        print("=" * 40)
    
    def _print_final_stats(self, stats: Dict):
        """Imprime estatísticas finais"""
        print(f"\n=== ESTATÍSTICAS FINAIS ===")
        print(f"Ciclos completados: {stats['cycles_completed']}")
        print(f"Total de candidatos coletados: {stats['total_candidates_collected']}")
        print(f"Total de candidatos validados: {stats['total_candidates_validated']}")
        print(f"Total de proxies ativos: {stats['total_active_proxies']}")
        print(f"Taxa de sucesso geral: {stats['overall_success_rate']:.1f}%")
        print(f"Modelo treinado: {'Sim' if stats['model_trained'] else 'Não'}")
        print(f"Arquivo de proxies ativos: {stats['active_proxies_file']}")
        print("=" * 40)

async def main():
    """Função principal"""
    print("🚀 Iniciando Proxygenesis AI")
    print("Sistema Inteligente de Geração e Validação de Proxies")
    print("=" * 50)
    
    # Criar instância do sistema
    system = ProxygenesisAI()
    
    # Mostrar estatísticas iniciais
    initial_stats = system.get_system_stats()
    print(f"Status inicial: {initial_stats}")
    
    # Executar sistema
    try:
        # Para demonstração, executar apenas 3 ciclos
        await system.run_continuous(max_cycles=3)
    except Exception as e:
        logger.error(f"Erro na execução principal: {e}")

if __name__ == "__main__":
    asyncio.run(main())