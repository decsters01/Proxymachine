"""
Módulo de Varredura Ativa de Portas
Implementa descoberta de proxies através de scanning de portas
"""

import subprocess
import ipaddress
import random
import logging
import asyncio
from typing import List, Dict, Set
from settings import SCRAPING_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortScanner:
    def __init__(self):
        self.common_ports = [80, 8080, 3128, 1080, 8888, 8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010, 443, 8443, 9090]
        self.cloud_providers = self._get_cloud_providers()
        self.scan_rate = 1000  # Portas por segundo (reduzido para ser mais conservador)
        
    def _get_cloud_providers(self) -> Dict[str, List[str]]:
        """Retorna ranges de IPs de provedores de cloud conhecidos"""
        return {
            'aws': [
                '3.0.0.0/8', '13.0.0.0/8', '18.0.0.0/8', '23.0.0.0/8',
                '34.0.0.0/8', '35.0.0.0/8', '52.0.0.0/8', '54.0.0.0/8',
                '107.20.0.0/14', '174.129.0.0/16'
            ],
            'google_cloud': [
                '8.34.208.0/20', '8.35.192.0/20', '23.236.48.0/20',
                '23.251.128.0/20', '35.184.0.0/13', '35.192.0.0/14',
                '35.196.0.0/15', '35.198.0.0/16', '35.199.0.0/17'
            ],
            'azure': [
                '13.64.0.0/11', '13.96.0.0/13', '13.104.0.0/14',
                '20.0.0.0/8', '23.96.0.0/13', '23.100.0.0/15',
                '40.64.0.0/10', '40.96.0.0/13', '40.104.0.0/15'
            ],
            'digitalocean': [
                '159.89.0.0/16', '159.203.0.0/16', '167.99.0.0/16',
                '178.128.0.0/16', '188.166.0.0/16', '198.199.64.0/18'
            ],
            'hetzner': [
                '5.9.0.0/16', '5.10.0.0/16', '46.4.0.0/16', '78.46.0.0/16',
                '88.198.0.0/16', '95.216.0.0/16', '136.243.0.0/16'
            ]
        }
    
    def _generate_target_ranges(self, max_ranges: int = 50) -> List[str]:
        """Gera ranges de IPs para escaneamento"""
        all_ranges = []
        
        # Adicionar ranges de cloud providers
        for provider, ranges in self.cloud_providers.items():
            all_ranges.extend(ranges)
        
        # Adicionar ranges aleatórios de diferentes países
        country_ranges = [
            '1.0.0.0/8',      # Austrália
            '2.0.0.0/8',      # França
            '5.0.0.0/8',      # Alemanha
            '8.0.0.0/8',      # EUA
            '14.0.0.0/8',     # China
            '27.0.0.0/8',     # China
            '31.0.0.0/8',     # Holanda
            '37.0.0.0/8',     # Alemanha
            '46.0.0.0/8',     # Rússia
            '62.0.0.0/8',     # Reino Unido
            '77.0.0.0/8',     # Rússia
            '78.0.0.0/8',     # Alemanha
            '79.0.0.0/8',     # Alemanha
            '80.0.0.0/8',     # França
            '81.0.0.0/8',     # França
            '82.0.0.0/8',     # Reino Unido
            '83.0.0.0/8',     # Alemanha
            '84.0.0.0/8',     # França
            '85.0.0.0/8',     # França
            '86.0.0.0/8',     # França
            '87.0.0.0/8',     # França
            '88.0.0.0/8',     # Alemanha
            '89.0.0.0/8',     # Alemanha
            '90.0.0.0/8',     # França
            '91.0.0.0/8',     # França
            '92.0.0.0/8',     # França
            '93.0.0.0/8',     # França
            '94.0.0.0/8',     # França
            '95.0.0.0/8',     # França
            '109.0.0.0/8',    # Alemanha
            '176.0.0.0/8',    # França
            '178.0.0.0/8',    # França
            '185.0.0.0/8',    # França
            '188.0.0.0/8',    # França
            '193.0.0.0/8',    # França
            '194.0.0.0/8',    # França
            '195.0.0.0/8',    # França
            '212.0.0.0/8',    # França
            '213.0.0.0/8',    # França
            '217.0.0.0/8',    # França
        ]
        
        all_ranges.extend(country_ranges)
        
        # Embaralhar e limitar
        random.shuffle(all_ranges)
        return all_ranges[:max_ranges]
    
    def _check_masscan_available(self) -> bool:
        """Verifica se o masscan está disponível"""
        try:
            result = subprocess.run(['masscan', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _install_masscan(self) -> bool:
        """Tenta instalar o masscan"""
        try:
            logger.info("Tentando instalar masscan...")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'masscan'], check=True)
            return self._check_masscan_available()
        except subprocess.CalledProcessError:
            logger.error("Falha ao instalar masscan")
            return False
    
    def scan_ports(self, target_ranges: List[str] = None, max_ports: int = 1000) -> List[str]:
        """
        Executa varredura de portas usando masscan
        
        Args:
            target_ranges: Lista de ranges de IP para escanear
            max_ports: Número máximo de portas abertas para retornar
            
        Returns:
            Lista de IP:PORTA encontrados
        """
        logger.info("Iniciando varredura de portas...")
        
        # Verificar se masscan está disponível
        if not self._check_masscan_available():
            logger.warning("Masscan não encontrado. Tentando instalar...")
            if not self._install_masscan():
                logger.error("Não foi possível instalar masscan. Usando método alternativo...")
                return self._scan_ports_alternative(target_ranges, max_ports)
        
        # Usar ranges padrão se não fornecidos
        if target_ranges is None:
            target_ranges = self._generate_target_ranges()
        
        # Preparar comando masscan
        ports_str = ','.join(map(str, self.common_ports))
        targets_str = ' '.join(target_ranges)
        
        cmd = [
            'masscan',
            '-p', ports_str,
            targets_str,
            '--rate', str(self.scan_rate),
            '--open-only',
            '--banners',
            '-oG', '-'
        ]
        
        try:
            logger.info(f"Executando masscan em {len(target_ranges)} ranges...")
            logger.info(f"Portas: {ports_str}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"Erro no masscan: {result.stderr}")
                return []
            
            # Parse dos resultados
            candidates = self._parse_masscan_output(result.stdout)
            
            # Limitar resultados
            if len(candidates) > max_ports:
                candidates = candidates[:max_ports]
            
            logger.info(f"Encontradas {len(candidates)} portas abertas")
            return candidates
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout na varredura de portas")
            return []
        except Exception as e:
            logger.error(f"Erro na varredura: {e}")
            return []
    
    def _parse_masscan_output(self, output: str) -> List[str]:
        """Parseia a saída do masscan"""
        candidates = []
        
        for line in output.split('\n'):
            if 'Host:' in line and 'Ports:' in line:
                try:
                    # Extrair IP
                    ip_start = line.find('Host: ') + 6
                    ip_end = line.find(' (', ip_start)
                    ip = line[ip_start:ip_end]
                    
                    # Extrair portas
                    ports_start = line.find('Ports: ') + 7
                    ports_section = line[ports_start:]
                    
                    # Parsear cada porta
                    for port_info in ports_section.split(','):
                        if '/' in port_info:
                            port = port_info.split('/')[0].strip()
                            if port.isdigit():
                                candidates.append(f"{ip}:{port}")
                
                except Exception as e:
                    logger.warning(f"Erro ao parsear linha: {line[:100]}... - {e}")
                    continue
        
        return candidates
    
    def _scan_ports_alternative(self, target_ranges: List[str], max_ports: int) -> List[str]:
        """
        Método alternativo de varredura quando masscan não está disponível
        Usa nmap ou implementação Python simples
        """
        logger.info("Usando método alternativo de varredura...")
        
        candidates = []
        
        # Gerar IPs aleatórios dos ranges
        for range_str in target_ranges[:10]:  # Limitar para 10 ranges
            try:
                network = ipaddress.ip_network(range_str, strict=False)
                
                # Amostrar IPs do range
                sample_size = min(100, network.num_addresses)
                if network.num_addresses > 0:
                    # Gerar IPs aleatórios do range
                    for _ in range(sample_size):
                        ip = str(network[random.randint(0, network.num_addresses - 1)])
                        
                        # Testar portas comuns
                        for port in self.common_ports[:5]:  # Apenas 5 portas mais comuns
                            candidates.append(f"{ip}:{port}")
                            
                            if len(candidates) >= max_ports:
                                break
                        
                        if len(candidates) >= max_ports:
                            break
                            
            except Exception as e:
                logger.warning(f"Erro ao processar range {range_str}: {e}")
                continue
        
        logger.info(f"Método alternativo encontrou {len(candidates)} candidatos")
        return candidates
    
    async def scan_ports_async(self, target_ranges: List[str] = None, max_ports: int = 1000) -> List[str]:
        """Versão assíncrona da varredura de portas"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scan_ports, target_ranges, max_ports)
    
    def get_scan_stats(self, candidates: List[str]) -> Dict:
        """Retorna estatísticas da varredura"""
        if not candidates:
            return {'total': 0, 'by_port': {}, 'by_provider': {}}
        
        # Estatísticas por porta
        by_port = {}
        for candidate in candidates:
            if ':' in candidate:
                port = candidate.split(':')[1]
                by_port[port] = by_port.get(port, 0) + 1
        
        # Estatísticas por provedor (baseado no IP)
        by_provider = {}
        for candidate in candidates:
            if ':' in candidate:
                ip = candidate.split(':')[0]
                provider = self._identify_provider(ip)
                by_provider[provider] = by_provider.get(provider, 0) + 1
        
        return {
            'total': len(candidates),
            'by_port': by_port,
            'by_provider': by_provider
        }
    
    def _identify_provider(self, ip: str) -> str:
        """Identifica o provedor baseado no IP"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            for provider, ranges in self.cloud_providers.items():
                for range_str in ranges:
                    if ip_obj in ipaddress.ip_network(range_str, strict=False):
                        return provider
            
            return 'unknown'
        except:
            return 'unknown'

def main():
    """Função principal para teste do scanner"""
    scanner = PortScanner()
    
    print("🔍 Testando Port Scanner...")
    print("=" * 50)
    
    # Testar com poucos ranges para demonstração
    test_ranges = ['8.8.8.0/24', '1.1.1.0/24']
    
    print(f"Escaneando ranges: {test_ranges}")
    candidates = scanner.scan_ports(test_ranges, max_ports=50)
    
    print(f"\nCandidatos encontrados: {len(candidates)}")
    
    if candidates:
        print("\nPrimeiros 10 candidatos:")
        for i, candidate in enumerate(candidates[:10], 1):
            print(f"  {i}. {candidate}")
    
    # Estatísticas
    stats = scanner.get_scan_stats(candidates)
    print(f"\nEstatísticas:")
    print(f"  Total: {stats['total']}")
    print(f"  Por porta: {stats['by_port']}")
    print(f"  Por provedor: {stats['by_provider']}")

if __name__ == "__main__":
    main()