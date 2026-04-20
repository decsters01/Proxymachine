# 🚀 PROXYGENESIS AI v2.0

## Sistema Inteligente de Geração e Validação de Proxies com Interface Web Futurista

![Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

### ✨ Funcionalidades

- **Coleta Híbrida**: Combina múltiplas fontes (listas públicas, Google Dorks, Shodan, varredura ativa)
- **Validação Inteligente**: Testa proxies em tempo real com verificação de anonimato
- **Machine Learning**: Modelo que aprende com proxies válidos para priorizar candidatos
- **Interface Web Moderna**: Dashboard futurista dark mode com atualizações em tempo real
- **Auto-Hospedável**: Fácil instalação em VPS para rodar 24/7

---

## 📋 Requisitos

- Python 3.8+
- VPS ou servidor local
- Conexão com internet

---

## 🔧 Instalação

### 1. Clone o repositório ou acesse a pasta do projeto

```bash
cd proxygenesis_ai
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Execute o servidor web

```bash
cd webapp
python server.py
```

### 4. Acesse a interface

Abra seu navegador e acesse:
```
http://localhost:8000
```

Ou na sua VPS:
```
http://SEU_IP:8000
```

---

## 🎮 Uso

### Interface Web

1. **Iniciar Sistema**: Clique em "INICIAR SISTEMA" para começar a coleta contínua
2. **Executar Ciclo**: Execute um único ciclo de coleta e validação
3. **Monitorar**: Acompanhe em tempo real as estatísticas e logs
4. **Baixar Proxies**: Exporte a lista de proxies ativos

### API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/status` | GET | Status atual do sistema |
| `/api/proxies/active` | GET | Lista de proxies ativos |
| `/api/system/start` | POST | Inicia o sistema |
| `/api/system/stop` | POST | Para o sistema |
| `/api/system/cycle` | POST | Executa um ciclo único |
| `/api/model/info` | GET | Informações do modelo ML |
| `/api/download/proxies` | GET | Download da lista de proxies |
| `/ws` | WebSocket | Conexão para atualizações em tempo real |

---

## 🏗️ Arquitetura

```
proxygenesis_ai/
├── webapp/
│   ├── server.py          # Servidor FastAPI
│   ├── templates/
│   │   └── index.html     # Interface principal
│   └── static/
│       ├── css/
│       │   └── style.css  # Estilos futuristas
│       └── js/
│           └── app.js     # Lógica frontend
├── main.py                # Orquestrador principal
├── hybrid_collector.py    # Coleta híbrida de proxies
├── checker.py             # Validação de proxies
├── trainer.py             # Treinamento do modelo ML
├── scraper.py             # Scraping de listas
├── port_scanner.py        # Varredura de portas
├── search_dorking.py      # Busca avançada
└── settings.py            # Configurações
```

---

## ⚙️ Configuração

Edite `settings.py` para personalizar:

- Fontes de proxies
- Timeout e concorrência
- Configurações de ML
- Caminhos de arquivos

---

## 🎨 Features da Interface

- **Design Cyberpunk/Futurista**: Visual dark com neon cyan e efeitos glow
- **Animações**: Partículas, grid animado, indicadores pulsantes
- **Responsivo**: Funciona em desktop e mobile
- **Tempo Real**: WebSocket para atualizações instantâneas
- **Logs Interativos**: Acompanhamento detalhado de atividades

---

## 🔒 Segurança

- Execute em ambiente isolado (VPS dedicada recomendada)
- Não use proxies para atividades ilegais
- Respeite os termos de serviço das fontes

---

## 📊 Como Funciona

1. **Coleta**: Agrega proxies de múltiplas fontes
2. **Priorização**: ML classifica candidatos por probabilidade de sucesso
3. **Validação**: Testa cada proxy com critérios rigorosos
4. **Armazenamento**: Salva proxies ativos em arquivo
5. **Aprendizado**: Atualiza modelo com novos dados
6. **Repetição**: Loop contínuo para manter lista atualizada

---

## 🛠️ Rodando em Produção (VPS)

### Systemd Service

Crie `/etc/systemd/system/proxygenesis.service`:

```ini
[Unit]
Description=Proxygenesis AI Web Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/proxygenesis_ai/webapp
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative e inicie:

```bash
systemctl enable proxygenesis
systemctl start proxygenesis
systemctl status proxygenesis
```

### Nginx Reverse Proxy (Opcional)

Para usar domínio próprio com HTTPS:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 📈 Melhorias Futuras

- [ ] Autenticação de usuários
- [ ] Banco de dados para histórico
- [ ] Gráficos e analytics
- [ ] API keys para Shodan integration
- [ ] Suporte a proxies SOCKS5
- [ ] Exportação em múltiplos formatos

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Abra issues e pull requests.

---

## 📄 Licença

MIT License - Use livremente.

---

## 💡 Dicas

- Execute em segundo plano com `nohup` ou `screen`
- Monitore uso de recursos da VPS
- Ajuste `max_concurrent_checks` conforme capacidade do servidor
- Use chaves de API (Shodan) para melhores resultados

---

**Proxygenesis AI** - Inteligência artificial aplicada à descoberta de proxies! 🚀
