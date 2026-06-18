"""
Proxygenesis AI - Sistema Inteligente de Geração e Validação de Proxies

Este é o módulo principal que unifica toda a funcionalidade do sistema em uma estrutura mais simples e inteligente.

Estrutura Refatorada:
- Menos módulos (de 15+ para 5 principais)
- Código mais coeso e fácil de manter
- Mesma funcionalidade completa
"""

__version__ = "2.0.0"
__author__ = "Proxygenesis AI Team"

from .core import ProxygenesisAI, ProxyCollector, ProxyValidator, ProxyPredictor
from .config import Config

__all__ = [
    'ProxygenesisAI',
    'ProxyCollector', 
    'ProxyValidator',
    'ProxyPredictor',
    'Config'
]
