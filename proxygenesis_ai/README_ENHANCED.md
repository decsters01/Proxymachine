# Proxygenesis AI v2.0 - Enhanced Edition

Sistema avançado de coleta, validação e predição de proxies com IA, auto-healing e API REST completa.

## 🚀 Novas Funcionalidades

### ✅ Implementadas nesta versão:

1. **Auto-Healing (Auto-Cura)**
   - Detecção automática de proxies instáveis
   - Remoção baseada em threshold de uptime
   - Histórico de verificações para decisão inteligente

2. **API REST Completa**
   - Autenticação por API Key
   - Endpoints para CRUD de proxies
   - Filtros avançados (país, protocolo, anonimato, velocidade, uptime)
   - Múltiplos formatos de exportação (JSON, CSV, YAML, TXT)
   - Documentação Swagger/OpenAPI

3. **Banco de Dados Histórico**
   - SQLite para armazenamento persistente
   - Histórico de ciclos e performance
   - Tracking de mudanças por proxy
   - Métricas de sistema

4. **ML Aprimorado**
   - XGBoost para predições mais precisas
   - Features avançadas: horário, geolocalização, ASN
   - Retreinamento automático com novos dados
   - Importância de features explicável

5. **Geolocalização**
   - Lookup automático de país/cidade
   - Informação de ASN/ISP
   - Enriquecimento de dados de proxies

## 📁 Estrutura do Projeto

```
proxygenesis_ai/
├── database/
│   └── db_manager.py       # Gerenciador do banco de dados
├── ml_enhanced/
│   └── predictor.py        # ML com XGBoost e features avançadas
├── api/
│   └── server.py           # API REST com autenticação
├── utils/
│   └── geoip.py            # Utilitários de geolocalização
├── webapp/
│   ├── server.py           # Servidor web principal
│   ├── templates/
│   │   └── index.html      # Interface web
│   └── static/
│       ├── css/style.css   # Estilos futuristas
│       └── js/app.js       # Lógica frontend
├── main.py                 # Orquestrador principal
├── checker.py              # Validação de proxies
├── hybrid_collector.py     # Coleta híbrida
├── trainer.py              # Treinamento ML
├── requirements.txt        # Dependências
├── start_enhanced.sh       # Script de inicialização
└── README.md               # Esta documentação
```

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- pip3

### Passos

```bash
cd /workspace/proxygenesis_ai

# Instalar dependências
pip install -r requirements.txt

# Ou usar o script automático
./start_enhanced.sh
```

## 🚀 Uso

### Iniciar o Sistema

```bash
# Método 1: Script automático (recomendado)
./start_enhanced.sh

# Método 2: Manualmente
python webapp/server.py  # Web UI na porta 8000
python api/server.py     # API na porta 8001
```

### Acessar Interfaces

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8001/docs
- **API Health**: http://localhost:8001/health

## 📖 API Usage

### Autenticação

Primeiro, crie uma API Key:

```bash
curl -X POST "http://localhost:8001/api/v1/keys" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-chave-mestre" \
  -d '{"name": "minha-app", "rate_limit": 1000}'
```

### Buscar Proxies com Filtros

```bash
curl "http://localhost:8001/api/v1/proxies?country=US&protocol=http&min_uptime=80&limit=100" \
  -H "X-API-Key: sua-api-key"
```

### Exportar Proxies

```bash
# JSON
curl "http://localhost:8001/api/v1/export?format=json&country=BR" \
  -H "X-API-Key: sua-api-key" -o proxies.json

# CSV
curl "http://localhost:8001/api/v1/export?format=csv&min_uptime=90" \
  -H "X-API-Key: sua-api-key" -o proxies.csv

# YAML
curl "http://localhost:8001/api/v1/export?format=yaml" \
  -H "X-API-Key: sua-api-key" -o proxies.yaml

# TXT (formato tradicional)
curl "http://localhost:8001/api/v1/export?format=txt&protocol=https" \
  -H "X-API-Key: sua-api-key" -o proxies.txt
```

### Auto-Healing

```bash
# Ativar auto-cura (remove proxies com uptime < 50%)
curl -X POST "http://localhost:8001/api/v1/autoheal?threshold_uptime=50&threshold_checks=5" \
  -H "X-API-Key: sua-api-key"
```

### Predição ML

```bash
# Predizer qualidade de um proxy
curl "http://localhost:8001/api/v1/predict/123" \
  -H "X-API-Key: sua-api-key"
```

### Estatísticas

```bash
curl "http://localhost:8001/api/v1/stats" \
  -H "X-API-Key: sua-api-key"
```

## 🔧 Configuração do Banco de Dados

O sistema usa SQLite automaticamente. O arquivo `proxygenesis.db` é criado na primeira execução.

### Tabelas Principais:

- **proxies**: Dados dos proxies com geolocalização
- **proxy_history**: Histórico de verificações
- **cycles**: Ciclos de coleta
- **ml_predictions**: Predições do modelo
- **performance_metrics**: Métricas de performance
- **api_keys**: Chaves de API

## 🤖 Machine Learning

### Features Usadas:

- Protocolo (http, https, socks4, socks5)
- Nível de anonimato
- Horário do dia
- Dia da semana
- Velocidade histórica
- Uptime percentage
- País/Região
- ASN

### Treinar Modelo:

```bash
python ml_enhanced/predictor.py
```

### Retreinar via API:

```bash
curl -X POST "http://localhost:8001/api/v1/ml/retrain" \
  -H "X-API-Key: sua-api-key"
```

## 🌍 Geolocalização

O sistema enriquece automaticamente os proxies com:

- País e código do país
- Cidade
- ASN (Autonomous System Number)
- ISP/Organização

Usa a API gratuita ip-api.com (rate limiting aplicado).

## 🔄 Auto-Healing

O sistema monitora continuamente:

1. Uptime de cada proxy
2. Número de verificações
3. Tendência de performance

Proxies são desativados automaticamente quando:
- Uptime < threshold (padrão: 50%)
- Mínimo de verificações atingido (padrão: 5)

## 📊 Endpoints da API

### Públicos (sem auth)
- `GET /` - Welcome message
- `GET /health` - Health check

### Protegidos (requer API Key)
- `GET /api/v1/proxies` - Listar proxies com filtros
- `GET /api/v1/proxies/{id}` - Detalhes do proxy
- `POST /api/v1/proxies` - Adicionar proxy
- `DELETE /api/v1/proxies/{id}` - Remover proxy
- `GET /api/v1/export` - Exportar em múltiplos formatos
- `GET /api/v1/stats` - Estatísticas do sistema
- `POST /api/v1/autoheal` - Trigger auto-healing
- `GET /api/v1/predict/{id}` - Predição ML
- `POST /api/v1/ml/retrain` - Retreinar modelo
- `GET /api/v1/keys` - Listar API keys
- `POST /api/v1/keys` - Criar API key
- `DELETE /api/v1/keys/{id}` - Revogar API key
- `GET /api/v1/cycles` - Histórico de ciclos
- `POST /api/v1/cycles/start` - Iniciar ciclo
- `POST /api/v1/cycles/{id}/complete` - Completar ciclo

## 🔒 Segurança

- API Keys com hash SHA-256
- Rate limiting configurável
- CORS habilitado para integração web
- Validação de inputs

## 📈 Performance

- Conexões pool otimizadas
- Índices no banco de dados
- Cache de previsões ML
- Thread-safe operations

## 🐛 Troubleshooting

### Database locked
```bash
rm proxygenesis.db
./start_enhanced.sh
```

### Module not found
```bash
pip install -r requirements.txt --upgrade
```

### Port already in use
Edite `webapp/server.py` e `api/server.py` para mudar as portas.

## 📝 License

MIT License - Use livremente!

## 🤝 Contributing

Pull requests são bem-vindos! 

## 📞 Support

Abra issues no GitHub para bugs ou feature requests.

---

**Proxygenesis AI v2.0** - Proxy Management Inteligente com IA 🚀
