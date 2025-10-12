"""
Coletor Híbrido para Descoberta de Proxies
Combina coleta passiva, varredura ativa e busca avançada
"""

import asyncio
import logging
import time
from typing import List, Dict, Set
from datetime import datetime

from scraper import ProxyScraper
from port_scanner import PortScanner
from search_dorking import SearchDorking
from settings import MAIN_LOOP_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridCollector:
    def __init__(self, shodan_api_key: str = None):
        self.scraper = ProxyScraper()
        self.port_scanner = PortScanner()
        self.search_dorker = SearchDorking(shodan_api_key)
        
        # Configurações de coleta
        self.max_candidates_per_source = 1000
        self.enable_port_scanning = True
        self.enable_search_dorking = True
        self.enable_public_lists = True
        
    async def collect_all_sources(self) -> Dict[str, List[str]]:
        """
        Coleta proxies de todas as fontes disponíveis
        
        Returns:
            Dicionário com proxies por fonte
        """
        logger.info("🚀 Iniciando coleta híbrida de proxies...")
        start_time = time.time()
        
        all_results = {}
        
        # Fonte A: Listas Públicas (Coleta Passiva)
        if self.enable_public_lists:
            logger.info("📥 Fonte A: Coletando de listas públicas...")
            try:
                public_proxies = await self.scraper.collect_all_proxies_async()
                all_results['public_lists'] = public_proxies
                logger.info(f"✅ Listas públicas: {len(public_proxies)} proxies")
            except Exception as e:
                logger.error(f"❌ Erro nas listas públicas: {e}")
                all_results['public_lists'] = []
        
        # Fonte B: Busca Avançada (Google Dorks + Shodan)
        if self.enable_search_dorking:
            logger.info("🔍 Fonte B: Buscando com métodos avançados...")
            try:
                search_results = await self.search_dorker.search_all_sources(
                    max_results=self.max_candidates_per_source
                )
                all_results.update(search_results)
                
                total_search = sum(len(proxies) for proxies in search_results.values())
                logger.info(f"✅ Busca avançada: {total_search} proxies")
            except Exception as e:
                logger.error(f"❌ Erro na busca avançada: {e}")
                all_results.update({
                    'google_dorks': [],
                    'shodan': [],
                    'pastebin': []
                })
        
        # Fonte C: Varredura Ativa de Portas
        if self.enable_port_scanning:
            logger.info("🔧 Fonte C: Executando varredura de portas...")
            try:
                # Usar ranges menores para demonstração
                test_ranges = [
                    '8.8.8.0/24', '1.1.1.0/24', '208.67.222.0/24',
                    '208.67.220.0/24', '9.9.9.0/24'
                ]
                
                port_scan_proxies = await self.port_scanner.scan_ports_async(
                    target_ranges=test_ranges,
                    max_ports=500
                )
                all_results['port_scan'] = port_scan_proxies
                logger.info(f"✅ Varredura de portas: {len(port_scan_proxies)} proxies")
            except Exception as e:
                logger.error(f"❌ Erro na varredura de portas: {e}")
                all_results['port_scan'] = []
        
        # Estatísticas finais
        total_time = time.time() - start_time
        total_proxies = sum(len(proxies) for proxies in all_results.values())
        
        logger.info(f"🎉 Coleta híbrida concluída em {total_time:.1f}s")
        logger.info(f"📊 Total de candidatos: {total_proxies}")
        
        # Mostrar estatísticas por fonte
        for source, proxies in all_results.items():
            logger.info(f"  {source}: {len(proxies)} proxies")
        
        return all_results
    
    def consolidate_candidates(self, all_results: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """
        Consolida candidatos de todas as fontes com metadados
        
        Args:
            all_results: Resultados de todas as fontes
            
        Returns:
            Lista de candidatos com metadados
        """
        logger.info("🔄 Consolidando candidatos de todas as fontes...")
        
        consolidated = []
        seen_proxies = set()
        
        for source, proxies in all_results.items():
            for proxy in proxies:
                # Evitar duplicatas
                if proxy in seen_proxies:
                    continue
                
                seen_proxies.add(proxy)
                
                # Adicionar metadados
                candidate = {
                    'proxy': proxy,
                    'source': source,
                    'discovery_method': self._get_discovery_method(source),
                    'quality_score': self._calculate_quality_score(proxy, source),
                    'timestamp': datetime.now().isoformat()
                }
                
                consolidated.append(candidate)
        
        logger.info(f"✅ Consolidados {len(consolidated)} candidatos únicos")
        return consolidated
    
    def _get_discovery_method(self, source: str) -> str:
        """Retorna o método de descoberta baseado na fonte"""
        method_mapping = {
            'public_lists': 'passive_collection',
            'google_dorks': 'search_dorking',
            'shodan': 'search_dorking',
            'pastebin': 'search_dorking',
            'port_scan': 'active_scanning'
        }
        return method_mapping.get(source, 'unknown')
    
    def _calculate_quality_score(self, proxy: str, source: str) -> float:
        """
        Calcula score de qualidade baseado na fonte e características do proxy
        
        Args:
            proxy: Proxy no formato IP:PORTA
            source: Fonte do proxy
            
        Returns:
            Score de qualidade (0.0 a 1.0)
        """
        base_scores = {
            'shodan': 0.9,           # Shodan tem alta qualidade
            'port_scan': 0.8,        # Varredura ativa encontra proxies "virgens"
            'google_dorks': 0.6,     # Google Dorks variável
            'pastebin': 0.4,         # Pastebin pode ter proxies antigos
            'public_lists': 0.3      # Listas públicas têm baixa qualidade
        }
        
        base_score = base_scores.get(source, 0.5)
        
        # Ajustar baseado nas características do proxy
        if ':' in proxy:
            ip, port = proxy.split(':', 1)
            
            # Portas comuns têm score mais alto
            common_ports = [80, 8080, 3128, 1080, 443]
            if int(port) in common_ports:
                base_score += 0.1
            
            # IPs de cloud providers têm score mais alto
            if self._is_cloud_provider_ip(ip):
                base_score += 0.1
            
            # IPs privados têm score mais baixo
            if self._is_private_ip(ip):
                base_score -= 0.2
        
        return min(1.0, max(0.0, base_score))
    
    def _is_cloud_provider_ip(self, ip: str) -> bool:
        """Verifica se o IP pertence a um provedor de cloud"""
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            
            cloud_ranges = [
                '3.0.0.0/8',      # AWS
                '13.0.0.0/8',     # AWS
                '18.0.0.0/8',     # AWS
                '34.0.0.0/8',     # Google Cloud
                '35.0.0.0/8',     # Google Cloud
                '20.0.0.0/8',     # Azure
                '40.0.0.0/8',     # Azure
            ]
            
            for range_str in cloud_ranges:
                if ip_obj in ipaddress.ip_network(range_str, strict=False):
                    return True
            
            return False
        except:
            return False
    
    def _is_private_ip(self, ip: str) -> bool:
        """Verifica se o IP é privado"""
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except:
            return False
    
    def prioritize_candidates(self, candidates: List[Dict[str, str]], 
                            max_candidates: int = None) -> List[Dict[str, str]]:
        """
        Prioriza candidatos baseado no score de qualidade
        
        Args:
            candidates: Lista de candidatos
            max_candidates: Número máximo de candidatos
            
        Returns:
            Lista priorizada de candidatos
        """
        if max_candidates is None:
            max_candidates = MAIN_LOOP_CONFIG['max_candidates_per_cycle']
        
        logger.info(f"🎯 Priorizando {len(candidates)} candidatos...")
        
        # Ordenar por score de qualidade (maior primeiro)
        prioritized = sorted(candidates, key=lambda x: x['quality_score'], reverse=True)
        
        # Limitar número de candidatos
        if len(prioritized) > max_candidates:
            prioritized = prioritized[:max_candidates]
        
        logger.info(f"✅ Priorizados {len(prioritized)} candidatos")
        
        # Mostrar top 10
        if prioritized:
            logger.info("Top 10 candidatos priorizados:")
            for i, candidate in enumerate(prioritized[:10], 1):
                logger.info(f"  {i:2d}. {candidate['proxy']} "
                          f"(fonte: {candidate['source']}, "
                          f"score: {candidate['quality_score']:.2f})")
        
        return prioritized
    
    def get_collection_stats(self, all_results: Dict[str, List[str]]) -> Dict:
        """Retorna estatísticas da coleta"""
        stats = {
            'total_sources': len(all_results),
            'total_candidates': sum(len(proxies) for proxies in all_results.values()),
            'by_source': {source: len(proxies) for source, proxies in all_results.items()},
            'by_method': {},
            'unique_candidates': 0
        }
        
        # Contar por método de descoberta
        method_counts = {}
        all_proxies = set()
        
        for source, proxies in all_results.items():
            method = self._get_discovery_method(source)
            method_counts[method] = method_counts.get(method, 0) + len(proxies)
            all_proxies.update(proxies)
        
        stats['by_method'] = method_counts
        stats['unique_candidates'] = len(all_proxies)
        
        return stats
    
    async def run_hybrid_collection(self) -> List[Dict[str, str]]:
        """
        Executa coleta híbrida completa
        
        Returns:
            Lista priorizada de candidatos
        """
        logger.info("🚀 Iniciando coleta híbrida completa...")
        
        # Coletar de todas as fontes
        all_results = await self.collect_all_sources()
        
        # Consolidar candidatos
        candidates = self.consolidate_candidates(all_results)
        
        # Priorizar candidatos
        prioritized = self.prioritize_candidates(candidates)
        
        # Estatísticas finais
        stats = self.get_collection_stats(all_results)
        logger.info(f"📊 Estatísticas finais:")
        logger.info(f"  Fontes: {stats['total_sources']}")
        logger.info(f"  Candidatos totais: {stats['total_candidates']}")
        logger.info(f"  Candidatos únicos: {stats['unique_candidates']}")
        logger.info(f"  Por método: {stats['by_method']}")
        
        return prioritized

async def main():
    """Função principal para teste do coletor híbrido"""
    print("🚀 Testando Coletor Híbrido...")
    print("=" * 60)
    
    # Criar coletor (sem chave Shodan para demonstração)
    collector = HybridCollector(shodan_api_key=None)
    
    # Executar coleta híbrida
    candidates = await collector.run_hybrid_collection()
    
    print(f"\n🎉 Coleta híbrida concluída!")
    print(f"📊 Candidatos priorizados: {len(candidates)}")
    
    if candidates:
        print(f"\nTop 10 candidatos:")
        for i, candidate in enumerate(candidates[:10], 1):
            print(f"  {i:2d}. {candidate['proxy']} "
                  f"(fonte: {candidate['source']}, "
                  f"score: {candidate['quality_score']:.2f})")

if __name__ == "__main__":
    asyncio.run(main())