"""
Módulo de Busca Avançada para Descoberta de Proxies
Implementa Google Dorks e integração com Shodan
"""

import requests
import re
import time
import random
import logging
from typing import List, Dict, Set
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
import asyncio
import aiohttp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchDorking:
    def __init__(self, shodan_api_key: str = None):
        self.shodan_api_key = shodan_api_key
        self.google_dorks = self._get_google_dorks()
        self.shodan_queries = self._get_shodan_queries()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def _get_google_dorks(self) -> List[str]:
        """Retorna lista de Google Dorks para encontrar proxies"""
        return [
            # Proxies HTTP
            'intext:"HTTP Proxy" filetype:txt "port: 8080"',
            'intext:"HTTP Proxy" filetype:txt "port: 3128"',
            'intext:"HTTP Proxy" filetype:txt "port: 80"',
            'intext:"HTTP Proxy" filetype:txt "port: 8000"',
            
            # Arquivos de configuração de proxy
            'inurl:"proxy.pac" filetype:pac',
            'inurl:"wpad.dat" filetype:dat',
            'inurl:"proxy.conf" filetype:conf',
            
            # Painéis de status de proxy
            'intitle:"Proxy Status"',
            'intitle:"Squid Proxy"',
            'intitle:"Proxy Server"',
            'intitle:"HTTP Proxy"',
            
            # Listas de proxy em sites
            'site:pastebin.com "proxy" "port"',
            'site:github.com "proxy list" filetype:txt',
            'site:raw.githubusercontent.com "proxy" "port"',
            
            # Proxies SOCKS
            'intext:"SOCKS Proxy" filetype:txt',
            'intext:"SOCKS5" filetype:txt',
            'intext:"SOCKS4" filetype:txt',
            
            # Proxies específicos por país
            'intext:"Brazil proxy" filetype:txt',
            'intext:"US proxy" filetype:txt',
            'intext:"Germany proxy" filetype:txt',
            'intext:"France proxy" filetype:txt',
            
            # Proxies de data centers
            'intext:"datacenter proxy" filetype:txt',
            'intext:"residential proxy" filetype:txt',
            'intext:"mobile proxy" filetype:txt',
            
            # Proxies com autenticação
            'intext:"proxy auth" filetype:txt',
            'intext:"proxy username" filetype:txt',
            'intext:"proxy password" filetype:txt',
        ]
    
    def _get_shodan_queries(self) -> List[str]:
        """Retorna queries para Shodan"""
        return [
            # Squid Proxy
            'product:"Squid http proxy"',
            'http.title:"Squid"',
            'http.html:"Squid"',
            
            # MikroTik Proxy
            'product:"MikroTik http proxy"',
            'http.title:"MikroTik"',
            
            # Outros proxies HTTP
            'http.title:"Proxy"',
            'http.html:"HTTP Proxy"',
            'http.html:"Proxy Server"',
            
            # Proxies por porta
            'port:3128 http.title:"Proxy"',
            'port:8080 http.title:"Proxy"',
            'port:8000 http.title:"Proxy"',
            
            # Proxies por país
            'country:"BR" port:3128',
            'country:"US" port:8080',
            'country:"DE" port:3128',
            'country:"FR" port:8080',
            
            # Proxies com banners específicos
            'http.title:"Proxy Status"',
            'http.title:"Proxy Server Status"',
            'http.html:"Proxy-Connection"',
            
            # Proxies SOCKS
            'product:"SOCKS"',
            'port:1080 product:"SOCKS"',
            'port:1081 product:"SOCKS"',
        ]
    
    def search_google_dorks(self, max_results: int = 100) -> List[str]:
        """
        Executa buscas usando Google Dorks
        
        Args:
            max_results: Número máximo de resultados
            
        Returns:
            Lista de proxies encontrados
        """
        logger.info("Iniciando busca com Google Dorks...")
        
        all_proxies = set()
        
        for dork in self.google_dorks[:10]:  # Limitar para 10 dorks para demonstração
            try:
                logger.info(f"Executando dork: {dork}")
                
                # Construir URL de busca
                search_url = f"https://www.google.com/search?q={quote(dork)}&num=20"
                
                # Fazer requisição
                response = self.session.get(search_url, timeout=10)
                response.raise_for_status()
                
                # Parsear resultados
                soup = BeautifulSoup(response.content, 'html.parser')
                proxies = self._extract_proxies_from_google_results(soup)
                
                all_proxies.update(proxies)
                logger.info(f"Dork '{dork}' encontrou {len(proxies)} proxies")
                
                # Delay entre buscas
                time.sleep(random.uniform(2, 5))
                
                if len(all_proxies) >= max_results:
                    break
                    
            except Exception as e:
                logger.warning(f"Erro no dork '{dork}': {e}")
                continue
        
        result = list(all_proxies)[:max_results]
        logger.info(f"Google Dorks encontrou {len(result)} proxies únicos")
        return result
    
    def _extract_proxies_from_google_results(self, soup: BeautifulSoup) -> List[str]:
        """Extrai proxies dos resultados do Google"""
        proxies = []
        
        # Procurar por links e texto que contenham proxies
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text()
            
            # Extrair proxies do href e texto
            proxies.extend(self._find_proxy_patterns(href))
            proxies.extend(self._find_proxy_patterns(text))
        
        # Procurar no texto da página
        page_text = soup.get_text()
        proxies.extend(self._find_proxy_patterns(page_text))
        
        return proxies
    
    def _find_proxy_patterns(self, text: str) -> List[str]:
        """Encontra padrões de proxy no texto"""
        proxies = []
        
        # Padrão IP:PORTA
        ip_port_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b'
        matches = re.findall(ip_port_pattern, text)
        
        for match in matches:
            if self._is_valid_proxy_format(match):
                proxies.append(match)
        
        return proxies
    
    def _is_valid_proxy_format(self, proxy: str) -> bool:
        """Valida formato de proxy"""
        try:
            if ':' not in proxy:
                return False
            
            ip, port = proxy.split(':', 1)
            
            # Validar IP
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                if not part.isdigit() or not 0 <= int(part) <= 255:
                    return False
            
            # Validar porta
            port_num = int(port)
            if not 1 <= port_num <= 65535:
                return False
            
            return True
        except:
            return False
    
    def search_shodan(self, max_results: int = 100) -> List[str]:
        """
        Busca proxies usando Shodan API
        
        Args:
            max_results: Número máximo de resultados
            
        Returns:
            Lista de proxies encontrados
        """
        if not self.shodan_api_key:
            logger.warning("Chave da API do Shodan não fornecida")
            return []
        
        logger.info("Iniciando busca com Shodan...")
        
        all_proxies = set()
        
        for query in self.shodan_queries[:5]:  # Limitar para 5 queries
            try:
                logger.info(f"Executando query Shodan: {query}")
                
                # Fazer requisição para Shodan
                url = f"https://api.shodan.io/shodan/host/search"
                params = {
                    'key': self.shodan_api_key,
                    'query': query,
                    'facets': 'port,country',
                    'page': 1
                }
                
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Extrair proxies dos resultados
                proxies = self._extract_proxies_from_shodan(data)
                all_proxies.update(proxies)
                
                logger.info(f"Query '{query}' encontrou {len(proxies)} proxies")
                
                # Delay entre requisições
                time.sleep(1)
                
                if len(all_proxies) >= max_results:
                    break
                    
            except Exception as e:
                logger.warning(f"Erro na query Shodan '{query}': {e}")
                continue
        
        result = list(all_proxies)[:max_results]
        logger.info(f"Shodan encontrou {len(result)} proxies únicos")
        return result
    
    def _extract_proxies_from_shodan(self, data: Dict) -> List[str]:
        """Extrai proxies dos resultados do Shodan"""
        proxies = []
        
        if 'matches' not in data:
            return proxies
        
        for match in data['matches']:
            try:
                ip = match.get('ip_str', '')
                port = match.get('port', '')
                
                if ip and port:
                    proxy = f"{ip}:{port}"
                    if self._is_valid_proxy_format(proxy):
                        proxies.append(proxy)
                        
            except Exception as e:
                logger.warning(f"Erro ao extrair proxy do resultado Shodan: {e}")
                continue
        
        return proxies
    
    def search_pastebin(self, max_results: int = 50) -> List[str]:
        """
        Busca proxies em Pastebin
        
        Args:
            max_results: Número máximo de resultados
            
        Returns:
            Lista de proxies encontrados
        """
        logger.info("Buscando proxies em Pastebin...")
        
        proxies = set()
        
        # Queries para Pastebin
        pastebin_queries = [
            'proxy list',
            'http proxy',
            'socks proxy',
            'proxy server',
            'free proxy'
        ]
        
        for query in pastebin_queries:
            try:
                # Buscar no Pastebin
                search_url = f"https://pastebin.com/search?q={quote(query)}"
                response = self.session.get(search_url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extrair links de pastes
                paste_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if '/raw/' in href:
                        paste_links.append(href)
                
                # Acessar cada paste
                for link in paste_links[:5]:  # Limitar para 5 pastes
                    try:
                        paste_url = f"https://pastebin.com{link}"
                        paste_response = self.session.get(paste_url, timeout=10)
                        paste_response.raise_for_status()
                        
                        # Extrair proxies do conteúdo
                        paste_proxies = self._find_proxy_patterns(paste_response.text)
                        proxies.update(paste_proxies)
                        
                        time.sleep(1)  # Delay entre pastes
                        
                    except Exception as e:
                        logger.warning(f"Erro ao acessar paste {link}: {e}")
                        continue
                
                time.sleep(2)  # Delay entre queries
                
            except Exception as e:
                logger.warning(f"Erro na busca Pastebin '{query}': {e}")
                continue
        
        result = list(proxies)[:max_results]
        logger.info(f"Pastebin encontrou {len(result)} proxies únicos")
        return result
    
    async def search_all_sources(self, max_results: int = 200) -> Dict[str, List[str]]:
        """
        Busca proxies em todas as fontes disponíveis
        
        Args:
            max_results: Número máximo de resultados por fonte
            
        Returns:
            Dicionário com proxies por fonte
        """
        logger.info("Iniciando busca em todas as fontes...")
        
        results = {}
        
        # Google Dorks
        try:
            results['google_dorks'] = self.search_google_dorks(max_results // 3)
        except Exception as e:
            logger.error(f"Erro no Google Dorks: {e}")
            results['google_dorks'] = []
        
        # Shodan
        try:
            results['shodan'] = self.search_shodan(max_results // 3)
        except Exception as e:
            logger.error(f"Erro no Shodan: {e}")
            results['shodan'] = []
        
        # Pastebin
        try:
            results['pastebin'] = self.search_pastebin(max_results // 3)
        except Exception as e:
            logger.error(f"Erro no Pastebin: {e}")
            results['pastebin'] = []
        
        # Estatísticas
        total_proxies = sum(len(proxies) for proxies in results.values())
        logger.info(f"Busca completa: {total_proxies} proxies encontrados")
        
        for source, proxies in results.items():
            logger.info(f"  {source}: {len(proxies)} proxies")
        
        return results

def main():
    """Função principal para teste do search dorking"""
    # Nota: Para usar Shodan, você precisa de uma chave API
    dorker = SearchDorking(shodan_api_key=None)
    
    print("🔍 Testando Search Dorking...")
    print("=" * 50)
    
    # Testar Google Dorks
    print("Testando Google Dorks...")
    google_proxies = dorker.search_google_dorks(max_results=20)
    print(f"Google Dorks encontrou: {len(google_proxies)} proxies")
    
    if google_proxies:
        print("Primeiros 5 proxies do Google:")
        for i, proxy in enumerate(google_proxies[:5], 1):
            print(f"  {i}. {proxy}")
    
    # Testar Pastebin
    print("\nTestando Pastebin...")
    pastebin_proxies = dorker.search_pastebin(max_results=10)
    print(f"Pastebin encontrou: {len(pastebin_proxies)} proxies")
    
    if pastebin_proxies:
        print("Primeiros 5 proxies do Pastebin:")
        for i, proxy in enumerate(pastebin_proxies[:5], 1):
            print(f"  {i}. {proxy}")
    
    print(f"\nTotal encontrado: {len(google_proxies) + len(pastebin_proxies)} proxies")

if __name__ == "__main__":
    main()