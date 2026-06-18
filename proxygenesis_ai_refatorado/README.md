# Proxygenesis AI Refatorado

Versão reestruturada e simplificada do Proxygenesis AI - Sistema Inteligente de Geração e Validação de Proxies.

## ✨ Melhorias da Versão Refatorada

### Redução de Complexidade
- **Antes**: 15+ módulos espalhados
- **Depois**: 3 módulos principais bem organizados

### Estrutura Simplificada

```
proxygenesis_ai_refatorado/
├── __init__.py       # Pacote principal
├── config.py         # Configurações unificadas (dataclass)
├── core.py           # Núcleo inteligente (todas as funcionalidades)
└── main.py           # Script de demonstração
```

### Principais Benefícios

1. **Menos Arquivos**: De ~15 arquivos Python para apenas 4
2. **Código Coeso**: Funcionalidades relacionadas agrupadas logicamente
3. **Configuração Unificada**: Todas as configurações em uma dataclass
4. **Tipagem Moderna**: Type hints em todo o código
5. **Fácil Manutenção**: Menos arquivos para gerenciar
6. **Mesma Funcionalidade**: Todas as features originais preservadas

## 🚀 Instalação

```bash
# Instalar dependências
pip install aiohttp requests beautifulsoup4 pandas numpy scikit-learn joblib

# Ou usar requirements.txt existente
pip install -r requirements.txt
```

## 💡 Uso Básico

### Exemplo Simples

```python
from proxygenesis_ai_refatorado import ProxygenesisAI, Config

# Criar configuração (opcional - tem valores padrão)
config = Config(
    max_candidates_per_cycle=5000,
    top_candidates_to_test=1000,
    retrain_frequency=3,
)

# Inicializar sistema
system = ProxygenesisAI(config=config)

# Executar um ciclo
import asyncio
cycle_stats = await system.run_cycle()

# Ou executar continuamente
await system.run_continuous(max_cycles=10)
```

### Exemplo com Configuração Personalizada

```python
from proxygenesis_ai_refatorado import ProxygenesisAI, Config

config = Config(
    # Fontes de proxies
    proxy_sources=[
        "https://www.free-proxy-list.net/",
        "https://www.proxyscrape.com/free-proxy-list",
    ],
    
    # Configurações de scraping
    timeout=15,
    max_retries=5,
    
    # Configurações de validação
    validation_timeout=10,
    max_concurrent_checks=200,
    
    # Configurações de ML
    n_estimators=150,
    max_depth=15,
    
    # Caminhos personalizados
    data_dir='/meu/diretorio/data',
    models_dir='/meu/diretorio/models',
)

system = ProxygenesisAI(config=config)
await system.run_continuous()
```

## 📊 Componentes Principais

### 1. Config (config.py)
Dataclass com todas as configurações do sistema:
- Fontes de proxies
- Timeouts e retries
- Parâmetros de ML
- Caminhos de arquivos

### 2. ProxyCollector (core.py)
Coleta híbrida de proxies:
- Listas públicas (web scraping)
- Busca avançada (Google Dorks)
- Varredura ativa de portas

### 3. ProxyValidator (core.py)
Validação assíncrona:
- Teste de conectividade
- Medição de tempo de resposta
- Verificação de anonimato

### 4. ProxyPredictor (core.py)
Machine Learning:
- Extração de features (IP, porta, metadados)
- Random Forest Classifier
- Predição de probabilidade
- Treinamento contínuo

### 5. ProxygenesisAI (core.py)
Orquestrador principal:
- Coordena todos os componentes
- Loop de operação contínua
- Persistência de dados
- Estatísticas do sistema

## 🔄 Ciclo de Operação

Cada ciclo executa 5 fases:

1. **Coleta Híbrida**: Coleta proxies de múltiplas fontes
2. **Priorização ML**: Usa modelo para priorizar candidatos
3. **Validação**: Testa proxies candidatos
4. **Atualização Dados**: Salva resultados para treinamento
5. **Retreinamento**: Atualiza modelo periodicamente

## 📈 Estatísticas

O sistema fornece estatísticas detalhadas:

```python
stats = system.get_stats()
print(f"Ciclos: {stats['cycles_completed']}")
print(f"Total candidatos: {stats['total_candidates']}")
print(f"Total ativos: {stats['total_active']}")
print(f"Sucesso: {stats['overall_success_rate']:.1f}%")
```

## 🎯 Comparação: Antes vs Depois

| Aspecto | Versão Antiga | Versão Refatorada |
|---------|--------------|-------------------|
| Arquivos Python | 15+ | 4 |
| Linhas de código | ~3000 | ~800 |
| Configurações | 3 arquivos | 1 dataclass |
| Imports | Múltiplos relativos | Simples e direto |
| Manutenibilidade | Baixa | Alta |
| Funcionalidades | Completas | Completas |

## 🛠️ Desenvolvimento

### Estrutura do Código

```python
# Importação simples
from proxygenesis_ai_refatorado import ProxygenesisAI, Config

# Uso direto sem caminhos complexos
config = Config()
system = ProxygenesisAI(config)
```

### Adicionar Novas Fontes

```python
config = Config(
    proxy_sources=[
        "https://nova-fonte.com/proxies",
        # ... mais fontes
    ]
)
```

### Customizar ML

```python
config = Config(
    n_estimators=200,
    max_depth=20,
    min_samples_split=3,
)
```

## 📝 License

Mesma licença do projeto original.

## 🤝 Contribuição

Contribuições são bem-vindas! A nova estrutura facilita:
- Adição de novas fontes
- Melhoria dos algoritmos de ML
- Otimização da validação
- Novas features

---

**Proxygenesis AI Refatorado** - Mais simples, mais inteligente, mais eficiente! 🚀
