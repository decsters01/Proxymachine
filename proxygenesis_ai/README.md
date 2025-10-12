# Proxygenesis AI

Sistema Inteligente de Geração e Validação de Proxies com Machine Learning

## 🎯 Objetivo

O Proxygenesis AI é um sistema em Python que autonomamente encontra, valida e "aprende" os padrões de proxies funcionais para priorizar a busca e validação de novos proxies com maior probabilidade de estarem ativos.

## 🧠 Conceito Principal

Em vez de "gerar" IPs do zero (que seria ineficaz), o sistema utiliza machine learning para **prever** a probabilidade de proxies candidatos estarem ativos, tornando o processo de verificação muito mais inteligente e eficiente.

## 🏗️ Arquitetura

### Fase 1: Coleta de Proxies Candidatos (Scraper)
- Varre a internet em busca de listas de proxies públicos
- Suporte a múltiplas fontes (GitHub, sites especializados, etc.)
- Coleta assíncrona para máxima performance
- Validação de formato IP:PORTA

### Fase 2: Validação de Proxies (Checker)
- Testa cada proxy candidato para determinar se está ativo
- Verificação de conectividade, tempo de resposta e anonimato
- Execução concorrente para máxima eficiência
- Critérios de sucesso configuráveis

### Fase 3: Machine Learning (Trainer)
- Engenharia de atributos avançada (IP, porta, performance, anonimato)
- Modelo RandomForest para classificação
- Aprendizado contínuo com novos dados
- Predição de probabilidade de ativação

### Fase 4: Loop de Refinamento
- Priorização inteligente de candidatos
- Retreinamento periódico do modelo
- Acúmulo de conhecimento ao longo do tempo
- Otimização contínua da taxa de sucesso

## 📁 Estrutura do Projeto

```
/proxygenesis_ai
├── main.py              # Orquestrador principal
├── scraper.py           # Módulo de coleta (Fase 1)
├── checker.py           # Módulo de validação (Fase 2)
├── trainer.py           # Módulo de ML (Fase 3)
├── settings.py          # Configurações
├── requirements.txt     # Dependências
├── README.md           # Documentação
├── /data
│   ├── training_data.csv   # Dados de treinamento
│   └── active_proxies.txt  # Proxies ativos encontrados
└── /models
    └── proxy_classifier.pkl # Modelo de ML salvo
```

## 🚀 Instalação

1. **Clone o repositório:**
```bash
git clone <repository-url>
cd proxygenesis_ai
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Execute o sistema:**
```bash
python main.py
```

## ⚙️ Configuração

Todas as configurações estão no arquivo `settings.py`:

- **Fontes de Proxies**: URLs para coleta
- **Configurações de Scraping**: Timeouts, delays, user-agents
- **Configurações de Validação**: URLs de teste, critérios de sucesso
- **Configurações de ML**: Parâmetros do modelo, frequência de retreinamento
- **Configurações do Loop**: Limites de candidatos, priorização

## 🔧 Uso

### Execução Básica
```python
from main import ProxygenesisAI
import asyncio

async def run_system():
    system = ProxygenesisAI()
    await system.run_continuous(max_cycles=5)

asyncio.run(run_system())
```

### Execução de Módulos Individuais

**Testar Scraper:**
```bash
python scraper.py
```

**Testar Checker:**
```bash
python checker.py
```

**Testar Trainer:**
```bash
python trainer.py
```

## 📊 Features Principais

### Scraper Inteligente
- ✅ Múltiplas fontes de proxies
- ✅ Parsing robusto de HTML
- ✅ Validação de formato IP:PORTA
- ✅ Coleta assíncrona
- ✅ Tratamento de erros robusto

### Validador Eficiente
- ✅ Teste de conectividade
- ✅ Verificação de anonimato
- ✅ Medição de performance
- ✅ Execução concorrente
- ✅ Timeouts configuráveis

### Machine Learning Avançado
- ✅ 20+ atributos de engenharia
- ✅ Modelo RandomForest
- ✅ Predição de probabilidade
- ✅ Aprendizado contínuo
- ✅ Persistência do modelo

### Loop de Otimização
- ✅ Priorização inteligente
- ✅ Retreinamento automático
- ✅ Acúmulo de conhecimento
- ✅ Estatísticas detalhadas
- ✅ Execução contínua

## 📈 Métricas e Estatísticas

O sistema coleta e exibe:
- Número de candidatos coletados
- Taxa de sucesso na validação
- Tempo médio de resposta
- Distribuição de níveis de anonimato
- Performance do modelo de ML
- Estatísticas por ciclo e gerais

## 🔍 Engenharia de Atributos

O modelo utiliza 20+ atributos:

**Atributos do IP:**
- Octetos individuais
- Soma, média e desvio padrão
- Tipo (privado, loopback, multicast)
- Padrões (repetidos, sequenciais)

**Atributos da Porta:**
- Número da porta
- Categorias (HTTP, HTTPS, SOCKS, Squid)
- Faixas (bem conhecidas, registradas, dinâmicas)
- Características numéricas

**Atributos de Performance:**
- Tempo de resposta
- Categorias de velocidade
- Disponibilidade

**Atributos de Anonimato:**
- Nível de anonimato
- Categorias específicas

## 🛠️ Personalização

### Adicionar Novas Fontes
Edite `settings.py` e adicione URLs à lista `PROXY_SOURCES`:

```python
PROXY_SOURCES = [
    "https://sua-nova-fonte.com/proxies",
    # ... outras fontes
]
```

### Ajustar Parâmetros de ML
Modifique `ML_CONFIG` em `settings.py`:

```python
ML_CONFIG = {
    'model_type': 'RandomForestClassifier',
    'n_estimators': 200,  # Mais árvores
    'max_depth': 15,      # Profundidade maior
    # ... outros parâmetros
}
```

### Configurar Validação
Ajuste `VALIDATION_CONFIG`:

```python
VALIDATION_CONFIG = {
    'test_url': 'https://api.ipify.org',  # URL diferente
    'timeout': 10,                        # Timeout maior
    'max_concurrent_checks': 200,         # Mais concorrência
}
```

## 📝 Logs

O sistema gera logs detalhados em:
- Console (tempo real)
- Arquivo `proxygenesis.log`

Níveis de log: INFO, WARNING, ERROR

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 🆘 Suporte

Para dúvidas ou problemas:
1. Verifique os logs
2. Consulte a documentação
3. Abra uma issue no GitHub

## 🔮 Roadmap

- [ ] Suporte a proxies SOCKS
- [ ] Interface web para monitoramento
- [ ] API REST para integração
- [ ] Suporte a proxies rotativos
- [ ] Análise de geolocalização
- [ ] Detecção de proxies premium
- [ ] Integração com bancos de dados
- [ ] Métricas avançadas de performance

---

**Proxygenesis AI** - Transformando a descoberta de proxies com inteligência artificial! 🚀