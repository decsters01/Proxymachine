#!/bin/bash
# Script de inicialização do Proxygenesis AI Web Server

echo "🚀 Iniciando Proxygenesis AI Web Server..."

# Verificar se está na pasta correta
cd "$(dirname "$0")"

# Verificar dependências
echo "📦 Verificando dependências..."
python3 -c "import fastapi" 2>/dev/null || {
    echo "⚠️ FastAPI não encontrada. Instalando dependências..."
    pip3 install -r requirements.txt
}

# Criar diretórios necessários
mkdir -p data models

# Iniciar servidor
echo "🌐 Iniciando servidor web na porta 8000..."
echo "📱 Acesse: http://localhost:8000"
echo ""
echo "Pressione Ctrl+C para parar"
echo "=========================================="

python3 webapp/server.py
