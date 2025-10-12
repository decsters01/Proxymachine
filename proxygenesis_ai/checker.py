"""
Módulo de Validação de Proxies
Implementa a Fase 2 do Proxygenesis AI
"""

import asyncio
import aiohttp
import time
import logging
from typing import List, Dict, Tuple
from settings import VALIDATION_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyChecker:
    def __init__(self):
        self.test_url = VALIDATION_CONFIG['test_url']
        self.timeout = VALIDATION_CONFIG['timeout']
        self.max_concurrent = VALIDATION_CONFIG['max_concurrent_checks']
        self.success_criteria = VALIDATION_CONFIG['success_criteria']
        
    async def check_proxy(self, proxy_string: str) -> Dict:
        """
        Verifica se um proxy está ativo e funcional
        
        Args:
            proxy_string: Proxy no formato IP:PORTA
            
        Returns:
            Dicionário com resultados da verificação
        """
        start_time = time.time()
        
        try:
            # Configurar proxy
            proxy_url = f"http://{proxy_string}"
            
            # Configurar timeout
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                ) as response:
                    
                    response_time = int((time.time() - start_time) * 1000)
                    
                    # Verificar critérios de sucesso
                    if (response.status == self.success_criteria['required_status_code'] and
                        response_time <= self.success_criteria['max_response_time']):
                        
                        # Verificar anonimato (opcional)
                        anonymity = await self._check_anonymity(response)
                        
                        return {
                            'proxy': proxy_string,
                            'is_active': True,
                            'response_time_ms': response_time,
                            'status_code': response.status,
                            'anonymity': anonymity,
                            'error': None
                        }
                    else:
                        return {
                            'proxy': proxy_string,
                            'is_active': False,
                            'response_time_ms': response_time,
                            'status_code': response.status,
                            'anonymity': 'unknown',
                            'error': f"Status {response.status} ou tempo de resposta {response_time}ms"
                        }
                        
        except asyncio.TimeoutError:
            response_time = int((time.time() - start_time) * 1000)
            return {
                'proxy': proxy_string,
                'is_active': False,
                'response_time_ms': response_time,
                'status_code': None,
                'anonymity': 'unknown',
                'error': 'Timeout'
            }
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            return {
                'proxy': proxy_string,
                'is_active': False,
                'response_time_ms': response_time,
                'status_code': None,
                'anonymity': 'unknown',
                'error': str(e)
            }
    
    async def _check_anonymity(self, response) -> str:
        """
        Verifica o nível de anonimato do proxy
        
        Args:
            response: Resposta HTTP do teste
            
        Returns:
            Nível de anonimato: 'elite', 'anonymous', 'transparent'
        """
        try:
            # Verificar headers que indicam anonimato
            headers = response.headers
            
            # Elite: Não revela IP real em headers
            if ('X-Forwarded-For' not in headers and 
                'X-Real-IP' not in headers and
                'Via' not in headers):
                return 'elite'
            
            # Anonymous: Revela que é proxy mas não o IP real
            elif ('X-Forwarded-For' in headers or 
                  'X-Real-IP' in headers or
                  'Via' in headers):
                return 'anonymous'
            
            # Transparent: Revela IP real
            else:
                return 'transparent'
                
        except:
            return 'unknown'
    
    async def validate_proxies(self, candidate_list: List[str]) -> List[Dict]:
        """
        Valida uma lista de proxies candidatos
        
        Args:
            candidate_list: Lista de proxies no formato IP:PORTA
            
        Returns:
            Lista de dicionários com resultados da validação
        """
        logger.info(f"Iniciando validação de {len(candidate_list)} proxies")
        
        # Limitar concorrência para evitar sobrecarga
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def check_with_semaphore(proxy):
            async with semaphore:
                return await self.check_proxy(proxy)
        
        # Criar tasks para todos os proxies
        tasks = [check_with_semaphore(proxy) for proxy in candidate_list]
        
        # Executar validação em lotes para evitar sobrecarga
        batch_size = self.max_concurrent
        results = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Erro na validação: {result}")
                else:
                    results.append(result)
            
            # Pequena pausa entre lotes
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.1)
        
        # Filtrar apenas proxies ativos
        active_proxies = [r for r in results if r['is_active']]
        
        logger.info(f"Validação concluída: {len(active_proxies)}/{len(candidate_list)} proxies ativos")
        
        return results  # Retornar todos os resultados, não apenas os ativos
    
    def validate_proxies_sync(self, candidate_list: List[str]) -> List[Dict]:
        """
        Versão síncrona da validação (para compatibilidade)
        
        Args:
            candidate_list: Lista de proxies no formato IP:PORTA
            
        Returns:
            Lista de dicionários com resultados da validação
        """
        return asyncio.run(self.validate_proxies(candidate_list))
    
    def get_active_proxies(self, validation_results: List[Dict]) -> List[str]:
        """
        Extrai apenas os proxies ativos dos resultados de validação
        
        Args:
            validation_results: Resultados da validação
            
        Returns:
            Lista de proxies ativos
        """
        return [r['proxy'] for r in validation_results if r['is_active']]
    
    def get_proxy_stats(self, validation_results: List[Dict]) -> Dict:
        """
        Calcula estatísticas dos resultados de validação
        
        Args:
            validation_results: Resultados da validação
            
        Returns:
            Dicionário com estatísticas
        """
        total = len(validation_results)
        active = len([r for r in validation_results if r['is_active']])
        
        if active > 0:
            active_times = [r['response_time_ms'] for r in validation_results if r['is_active']]
            avg_response_time = sum(active_times) / len(active_times)
            min_response_time = min(active_times)
            max_response_time = max(active_times)
        else:
            avg_response_time = 0
            min_response_time = 0
            max_response_time = 0
        
        # Contar níveis de anonimato
        anonymity_counts = {}
        for result in validation_results:
            if result['is_active']:
                anonymity = result['anonymity']
                anonymity_counts[anonymity] = anonymity_counts.get(anonymity, 0) + 1
        
        return {
            'total_tested': total,
            'active_count': active,
            'success_rate': (active / total * 100) if total > 0 else 0,
            'avg_response_time_ms': avg_response_time,
            'min_response_time_ms': min_response_time,
            'max_response_time_ms': max_response_time,
            'anonymity_distribution': anonymity_counts
        }

def main():
    """Função principal para teste do checker"""
    checker = ProxyChecker()
    
    # Lista de teste
    test_proxies = [
        "8.8.8.8:80",
        "1.1.1.1:80",
        "127.0.0.1:8080",  # Provavelmente não funcionará
        "invalid.proxy:9999"  # Definitivamente não funcionará
    ]
    
    print("Testando validação de proxies...")
    results = checker.validate_proxies_sync(test_proxies)
    
    # Mostrar resultados
    for result in results:
        status = "✓ ATIVO" if result['is_active'] else "✗ INATIVO"
        print(f"{result['proxy']}: {status} ({result['response_time_ms']}ms)")
        if result['error']:
            print(f"  Erro: {result['error']}")
    
    # Mostrar estatísticas
    stats = checker.get_proxy_stats(results)
    print(f"\nEstatísticas:")
    print(f"  Total testado: {stats['total_tested']}")
    print(f"  Ativos: {stats['active_count']}")
    print(f"  Taxa de sucesso: {stats['success_rate']:.1f}%")
    print(f"  Tempo médio de resposta: {stats['avg_response_time_ms']:.1f}ms")

if __name__ == "__main__":
    main()