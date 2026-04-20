"""
FastAPI Web Server para Proxygenesis AI
Interface web moderna e futurista para controle do sistema
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from main import ProxygenesisAI
from settings import PATHS

# Inicializar FastAPI
app = FastAPI(
    title="Proxygenesis AI",
    description="Sistema Inteligente de Geração e Validação de Proxies",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
static_path = Path(__file__).parent / "webapp" / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Variáveis globais
system_instance: Optional[ProxygenesisAI] = None
system_running = False
system_task: Optional[asyncio.Task] = None
connected_websockets: List[WebSocket] = []


class ConnectionManager:
    """Gerencia conexões WebSocket"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Envia mensagem para todos os clientes conectados"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remover conexões desconectadas
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


def get_system() -> ProxygenesisAI:
    """Obtém ou cria instância do sistema"""
    global system_instance
    if system_instance is None:
        system_instance = ProxygenesisAI()
    return system_instance


@app.on_event("startup")
async def startup_event():
    """Inicializa o sistema na inicialização"""
    global system_instance
    system_instance = get_system()
    print("🚀 Proxygenesis AI Web Server iniciado!")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve a página principal"""
    template_path = Path(__file__).parent / "webapp" / "templates" / "index.html"
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Template não encontrado</h1>", status_code=404)


@app.get("/api/status")
async def get_status():
    """Retorna o status atual do sistema"""
    system = get_system()
    stats = system.get_system_stats()
    
    return {
        "status": "running" if system_running else "stopped",
        "cycles_completed": stats['cycles_completed'],
        "total_candidates": stats['total_candidates_collected'],
        "total_validated": stats['total_candidates_validated'],
        "total_active": stats['total_active_proxies'],
        "success_rate": stats['overall_success_rate'],
        "model_trained": stats['model_trained'],
        "uptime": datetime.now().isoformat()
    }


@app.get("/api/proxies/active")
async def get_active_proxies(limit: int = 100):
    """Retorna lista de proxies ativos"""
    active_file = Path(PATHS['active_proxies'])
    
    if not active_file.exists():
        return {"proxies": [], "count": 0}
    
    try:
        with open(active_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Pegar últimos proxies (mais recentes)
        proxies = [line.strip() for line in lines[-limit:] if line.strip()]
        
        return {
            "proxies": proxies,
            "count": len(proxies),
            "total_available": len(lines)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/history")
async def get_stats_history():
    """Retorna histórico de estatísticas (simulado)"""
    # Em produção, isso viria de um banco de dados
    return {
        "history": [],
        "message": "Histórico será implementado em breve"
    }


@app.post("/api/system/start")
async def start_system(background_tasks: BackgroundTasks):
    """Inicia o sistema em background"""
    global system_running, system_task
    
    if system_running:
        return {"message": "Sistema já está em execução"}
    
    system_running = True
    system = get_system()
    
    async def run_system():
        """Executa o sistema continuamente"""
        global system_running
        try:
            while system_running:
                cycle_stats = await system.run_cycle()
                
                # Notificar clientes WebSocket
                await manager.broadcast({
                    "type": "cycle_complete",
                    "data": cycle_stats,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Aguardar antes do próximo ciclo
                await asyncio.sleep(60)
                
        except Exception as e:
            await manager.broadcast({
                "type": "error",
                "message": str(e)
            })
            system_running = False
    
    system_task = asyncio.create_task(run_system())
    
    return {"message": "Sistema iniciado com sucesso"}


@app.post("/api/system/stop")
async def stop_system():
    """Para o sistema"""
    global system_running
    
    if not system_running:
        return {"message": "Sistema já está parado"}
    
    system_running = False
    
    return {"message": "Sistema sendo parado..."}


@app.post("/api/system/cycle")
async def run_single_cycle(background_tasks: BackgroundTasks):
    """Executa um único ciclo"""
    system = get_system()
    
    async def run_and_notify():
        cycle_stats = await system.run_cycle()
        
        await manager.broadcast({
            "type": "cycle_complete",
            "data": cycle_stats,
            "timestamp": datetime.now().isoformat()
        })
        
        return cycle_stats
    
    task = asyncio.create_task(run_and_notify())
    
    return {"message": "Ciclo iniciado", "task_id": id(task)}


@app.get("/api/model/info")
async def get_model_info():
    """Retorna informações sobre o modelo de ML"""
    system = get_system()
    
    model_path = Path(PATHS['model_file'])
    training_data_path = Path(PATHS['training_data'])
    
    model_exists = model_path.exists()
    training_samples = 0
    
    if training_data_path.exists():
        import pandas as pd
        df = pd.read_csv(training_data_path)
        training_samples = len(df)
    
    return {
        "model_trained": model_exists and system.trainer.is_trained,
        "model_path": str(model_path),
        "training_samples": training_samples,
        "last_trained": None  # Implementar quando salvar metadata
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para atualizações em tempo real"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Manter conexão ativa
            data = await websocket.receive_text()
            
            # Se receber mensagem, responder com status atual
            if data == "get_status":
                system = get_system()
                stats = system.get_system_stats()
                await websocket.send_json({
                    "type": "status_update",
                    "data": stats
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


@app.get("/api/download/proxies")
async def download_proxies():
    """Download da lista de proxies ativos"""
    active_file = Path(PATHS['active_proxies'])
    
    if not active_file.exists():
        raise HTTPException(status_code=404, detail="Nenhum proxy disponível")
    
    return FileResponse(
        path=str(active_file),
        filename="active_proxies.txt",
        media_type="text/plain"
    )


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
