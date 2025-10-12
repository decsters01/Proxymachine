"""
Configurações do Proxygenesis AI
Contém todas as configurações necessárias para o sistema
"""

# URLs de fontes de proxies
PROXY_SOURCES = [
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
]

# Configurações de scraping
SCRAPING_CONFIG = {
    'timeout': 10,
    'max_retries': 3,
    'delay_between_requests': 1,  # segundos
    'concurrent_requests': 50,
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
}

# Configurações de validação
VALIDATION_CONFIG = {
    'test_url': 'http://httpbin.org/ip',
    'timeout': 5,
    'max_concurrent_checks': 100,
    'success_criteria': {
        'max_response_time': 10000,  # 10 segundos em ms
        'required_status_code': 200
    }
}

# Configurações de ML
ML_CONFIG = {
    'model_type': 'RandomForestClassifier',
    'test_size': 0.2,
    'random_state': 42,
    'n_estimators': 100,
    'max_depth': 10,
    'min_samples_split': 5,
    'min_samples_leaf': 2
}

# Configurações do loop principal
MAIN_LOOP_CONFIG = {
    'max_candidates_per_cycle': 10000,
    'top_candidates_to_test': 2000,
    'retrain_frequency': 5,  # retreinar a cada 5 ciclos
    'min_training_samples': 1000
}

# Caminhos de arquivos
PATHS = {
    'data_dir': 'data',
    'models_dir': 'models',
    'training_data': 'data/training_data.csv',
    'active_proxies': 'data/active_proxies.txt',
    'model_file': 'models/proxy_classifier.pkl'
}

# Portas comuns de proxies
COMMON_PORTS = [80, 8080, 3128, 8081, 1080, 8888, 9999, 3129, 8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010]