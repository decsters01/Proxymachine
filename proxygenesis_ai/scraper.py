"""
Módulo de Scraping para Coleta de Proxies Candidatos
Implementa a Fase 1 do Proxygenesis AI
"""

import requests
import re
import time
import random
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Set
from settings import PROXY_SOURCES, SCRAPING_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(SCRAPING_CONFIG['user_agents'])
        })
        self.proxies_found = set()
        
    def fetch_proxies_from_url(self, url: str) -> List[str]:
        """
        Coleta proxies de uma URL específica
        
        Args:
            url: URL da fonte de proxies
            
        Returns:
            Lista de proxies no formato IP:PORTA
        """
        proxies = []
        
        try:
            logger.info(f"Coletando proxies de: {url}")
            
            # Fazer requisição com retry
            for attempt in range(SCRAPING_CONFIG['max_retries']):
                try:
                    response = self.session.get(
                        url, 
                        timeout=SCRAPING_CONFIG['timeout'],
                        headers={'User-Agent': random.choice(SCRAPING_CONFIG['user_agents'])}
                    )
                    response.raise_for_status()
                    break
                except Exception as e:
                    if attempt == SCRAPING_CONFIG['max_retries'] - 1:
                        logger.error(f"Falha ao acessar {url} após {SCRAPING_CONFIG['max_retries']} tentativas: {e}")
                        return []
                    time.sleep(2 ** attempt)  # Backoff exponencial
            
            # Parse do HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrair proxies usando diferentes estratégias
            proxies.extend(self._extract_from_tables(soup))
            proxies.extend(self._extract_from_text(soup))
            proxies.extend(self._extract_from_raw_text(response.text))
            
            # Validar formato dos proxies
            valid_proxies = [p for p in proxies if self._is_valid_proxy_format(p)]
            
            logger.info(f"Encontrados {len(valid_proxies)} proxies válidos em {url}")
            return valid_proxies
            
        except Exception as e:
            logger.error(f"Erro ao processar {url}: {e}")
            return []
    
    def _extract_from_tables(self, soup: BeautifulSoup) -> List[str]:
        """Extrai proxies de tabelas HTML"""
        proxies = []
        
        # Procurar por tabelas
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Tentar extrair IP e porta das primeiras duas colunas
                    ip_text = cells[0].get_text(strip=True)
                    port_text = cells[1].get_text(strip=True)
                    
                    if self._is_valid_ip(ip_text) and self._is_valid_port(port_text):
                        proxies.append(f"{ip_text}:{port_text}")
        
        return proxies
    
    def _extract_from_text(self, soup: BeautifulSoup) -> List[str]:
        """Extrai proxies de texto HTML"""
        proxies = []
        
        # Procurar por padrões de IP:PORTA em todo o texto
        text = soup.get_text()
        proxy_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b'
        matches = re.findall(proxy_pattern, text)
        
        for match in matches:
            if self._is_valid_proxy_format(match):
                proxies.append(match)
        
        return proxies
    
    def _extract_from_raw_text(self, text: str) -> List[str]:
        """Extrai proxies de texto bruto (para URLs que retornam listas simples)"""
        proxies = []
        
        # Padrão mais específico para IP:PORTA
        proxy_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b'
        matches = re.findall(proxy_pattern, text)
        
        for match in matches:
            if self._is_valid_proxy_format(match):
                proxies.append(match)
        
        return proxies
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Valida se uma string é um IP válido"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not part.isdigit() or not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False
    
    def _is_valid_port(self, port: str) -> bool:
        """Valida se uma string é uma porta válida"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except:
            return False
    
    def _is_valid_proxy_format(self, proxy: str) -> bool:
        """Valida se uma string está no formato IP:PORTA"""
        try:
            if ':' not in proxy:
                return False
            
            ip, port = proxy.split(':', 1)
            return self._is_valid_ip(ip) and self._is_valid_port(port)
        except:
            return False
    
    async def fetch_proxies_async(self, url: str) -> List[str]:
        """
        Versão assíncrona para coleta de proxies
        """
        proxies = []
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=SCRAPING_CONFIG['timeout']),
                headers={'User-Agent': random.choice(SCRAPING_CONFIG['user_agents'])}
            ) as session:
                
                async with session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        soup = BeautifulSoup(text, 'html.parser')
                        
                        # Extrair proxies usando as mesmas estratégias
                        proxies.extend(self._extract_from_tables(soup))
                        proxies.extend(self._extract_from_text(soup))
                        proxies.extend(self._extract_from_raw_text(text))
                        
                        # Validar formato
                        valid_proxies = [p for p in proxies if self._is_valid_proxy_format(p)]
                        logger.info(f"Encontrados {len(valid_proxies)} proxies válidos em {url}")
                        return valid_proxies
                    else:
                        logger.warning(f"Status {response.status} para {url}")
                        return []
                        
        except Exception as e:
            logger.error(f"Erro assíncrono ao processar {url}: {e}")
            return []
    
    def collect_all_proxies(self) -> List[str]:
        """
        Coleta proxies de todas as fontes configuradas
        
        Returns:
            Lista única de todos os proxies encontrados
        """
        all_proxies = set()
        
        logger.info(f"Iniciando coleta de proxies de {len(PROXY_SOURCES)} fontes")
        
        for i, url in enumerate(PROXY_SOURCES):
            try:
                proxies = self.fetch_proxies_from_url(url)
                all_proxies.update(proxies)
                
                logger.info(f"Fonte {i+1}/{len(PROXY_SOURCES)}: {len(proxies)} proxies")
                
                # Delay entre requisições para evitar bloqueios
                if i < len(PROXY_SOURCES) - 1:
                    time.sleep(SCRAPING_CONFIG['delay_between_requests'])
                    
            except Exception as e:
                logger.error(f"Erro ao processar fonte {url}: {e}")
                continue
        
        result = list(all_proxies)
        logger.info(f"Coleta concluída: {len(result)} proxies únicos encontrados")
        return result
    
    async def collect_all_proxies_async(self) -> List[str]:
        """
        Versão assíncrona para coleta de proxies (mais rápida)
        """
        logger.info(f"Iniciando coleta assíncrona de proxies de {len(PROXY_SOURCES)} fontes")
        
        # Criar tasks para todas as URLs
        tasks = []
        for url in PROXY_SOURCES:
            task = self.fetch_proxies_async(url)
            tasks.append(task)
        
        # Executar todas as tasks concorrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolidar resultados
        all_proxies = set()
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Erro na fonte {i+1}: {result}")
            else:
                all_proxies.update(result)
                logger.info(f"Fonte {i+1}: {len(result)} proxies")
        
        final_result = list(all_proxies)
        logger.info(f"Coleta assíncrona concluída: {len(final_result)} proxies únicos encontrados")
        return final_result

def main():
    """Função principal para teste do scraper"""
    scraper = ProxyScraper()
    
    # Teste da versão síncrona
    print("Testando coleta síncrona...")
    proxies = scraper.collect_all_proxies()
    print(f"Proxies encontrados: {len(proxies)}")
    
    # Mostrar alguns exemplos
    if proxies:
        print("Primeiros 10 proxies encontrados:")
        for proxy in proxies[:10]:
            print(f"  {proxy}")

if __name__ == "__main__":
    main()