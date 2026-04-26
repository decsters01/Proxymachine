"""
Configurações Unificadas do Proxygenesis AI

Todas as configurações do sistema em um único lugar para facilitar manutenção e personalização.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class Config:
    """Configurações principais do sistema"""
    
    # URLs de fontes de proxies públicos
    proxy_sources: List[str] = field(default_factory=lambda: [
        "https://www.free-proxy-list.net/",
        "https://www.proxyscrape.com/free-proxy-list",
        "https://www.proxy-list.download/HTTP",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt"
    ])
    
    # Configurações de scraping
    timeout: int = 10
    max_retries: int = 3
    delay_between_requests: float = 1.0
    concurrent_requests: int = 50
    user_agents: List[str] = field(default_factory=lambda: [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ])
    
    # Configurações de validação
    test_url: str = 'http://httpbin.org/ip'
    validation_timeout: int = 5
    max_concurrent_checks: int = 100
    max_response_time: int = 10000  # ms
    required_status_code: int = 200
    
    # Configurações de Machine Learning
    model_type: str = 'RandomForestClassifier'
    test_size: float = 0.2
    random_state: int = 42
    n_estimators: int = 100
    max_depth: int = 10
    min_samples_split: int = 5
    min_samples_leaf: int = 2
    
    # Configurações do loop principal
    max_candidates_per_cycle: int = 10000
    top_candidates_to_test: int = 2000
    retrain_frequency: int = 5
    min_training_samples: int = 1000
    
    # Caminhos de arquivos
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / 'data')
    models_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / 'models')
    training_data_file: str = 'training_data.csv'
    active_proxies_file: str = 'active_proxies.txt'
    model_file: str = 'proxy_classifier.pkl'
    
    # Portas comuns de proxies
    common_ports: List[int] = field(default_factory=lambda: [
        80, 8080, 3128, 8081, 1080, 8888, 9999, 3129, 
        8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010
    ])
    
    # Configurações de coleta híbrida
    enable_port_scanning: bool = True
    enable_search_dorking: bool = True
    enable_public_lists: bool = True
    max_candidates_per_source: int = 1000
    
    # Chaves de API opcionais
    shodan_api_key: str = None
    
    @property
    def training_data_path(self) -> Path:
        """Retorna o caminho completo para o arquivo de dados de treinamento"""
        return self.data_dir / self.training_data_file
    
    @property
    def active_proxies_path(self) -> Path:
        """Retorna o caminho completo para o arquivo de proxies ativos"""
        return self.data_dir / self.active_proxies_file
    
    @property
    def model_path(self) -> Path:
        """Retorna o caminho completo para o arquivo do modelo"""
        return self.models_dir / self.model_file
    
    def __post_init__(self):
        """Garante que os diretórios existam após a inicialização"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte configurações para dicionário"""
        return {
            'proxy_sources': self.proxy_sources,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'user_agents': self.user_agents,
            'test_url': self.test_url,
            'validation_timeout': self.validation_timeout,
            'max_concurrent_checks': self.max_concurrent_checks,
            'model_type': self.model_type,
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'max_candidates_per_cycle': self.max_candidates_per_cycle,
            'top_candidates_to_test': self.top_candidates_to_test,
            'retrain_frequency': self.retrain_frequency,
            'min_training_samples': self.min_training_samples,
        }
