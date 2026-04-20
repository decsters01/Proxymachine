/**
 * PROXYGENESIS AI - APLICAÇÃO FRONTEND
 * Interface interativa com atualizações em tempo real
 */

// Variáveis globais
let ws = null;
let systemRunning = false;
let updateInterval = null;

// Elementos do DOM
const elements = {
    // Status
    systemStatus: document.getElementById('systemStatus'),
    statusIndicator: document.querySelector('.status-indicator'),
    statusText: document.querySelector('.status-text'),
    
    // Estatísticas
    cyclesCount: document.getElementById('cyclesCount'),
    totalCandidates: document.getElementById('totalCandidates'),
    activeProxies: document.getElementById('activeProxies'),
    successRate: document.getElementById('successRate'),
    
    // Botões
    btnStart: document.getElementById('btnStart'),
    btnStop: document.getElementById('btnStop'),
    btnCycle: document.getElementById('btnCycle'),
    
    // ML
    modelTrained: document.getElementById('modelTrained'),
    trainingSamples: document.getElementById('trainingSamples'),
    mlIndicator: document.getElementById('mlIndicator'),
    
    // Proxies
    proxiesList: document.getElementById('proxiesList'),
    proxyCount: document.getElementById('proxyCount'),
    
    // Log
    logContainer: document.getElementById('logContainer')
};

/**
 * Inicializa a aplicação
 */
document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    loadStatus();
    connectWebSocket();
    startAutoUpdate();
    
    addLog('Sistema inicializado. Conectado à interface.', 'info');
});

/**
 * Inicializa efeito de partículas no background
 */
function initParticles() {
    const particlesContainer = document.getElementById('particles');
    const particleCount = 50;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 15 + 's';
        particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
        particlesContainer.appendChild(particle);
    }
}

/**
 * Conecta ao WebSocket para atualizações em tempo real
 */
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            addLog('Conectado ao servidor em tempo real', 'success');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onclose = () => {
            addLog('Conexão WebSocket fechada. Reconectando...', 'warning');
            setTimeout(connectWebSocket, 3000);
        };
        
        ws.onerror = (error) => {
            console.error('Erro WebSocket:', error);
            addLog('Erro na conexão em tempo real', 'error');
        };
    } catch (error) {
        console.error('Erro ao criar WebSocket:', error);
    }
}

/**
 * Manipula mensagens do WebSocket
 */
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'cycle_complete':
            handleCycleComplete(data.data);
            break;
        case 'status_update':
            updateUI(data.data);
            break;
        case 'error':
            addLog(`Erro: ${data.message}`, 'error');
            break;
    }
}

/**
 * Handle de ciclo completo
 */
function handleCycleComplete(cycleData) {
    addLog(`Ciclo ${cycleData.cycle} concluído!`, 'success');
    addLog(`Proxies ativos encontrados: ${cycleData.active_proxies_found}`, 'success');
    
    if (cycleData.model_retrained) {
        addLog('Modelo de ML retreinado com sucesso!', 'success');
    }
    
    // Atualizar estatísticas
    loadStatus();
    loadActiveProxies();
}

/**
 * Carrega status atual do sistema
 */
async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        updateUI(data);
    } catch (error) {
        console.error('Erro ao carregar status:', error);
    }
}

/**
 * Atualiza interface com dados do sistema
 */
function updateUI(data) {
    // Atualizar status do sistema
    systemRunning = data.status === 'running';
    updateSystemStatus(systemRunning);
    
    // Atualizar estatísticas
    if (elements.cyclesCount) elements.cyclesCount.textContent = data.cycles_completed || 0;
    if (elements.totalCandidates) elements.totalCandidates.textContent = formatNumber(data.total_candidates || 0);
    if (elements.activeProxies) elements.activeProxies.textContent = formatNumber(data.total_active || 0);
    if (elements.successRate) elements.successRate.textContent = `${(data.success_rate || 0).toFixed(1)}%`;
    
    // Atualizar modelo ML
    loadModelInfo();
}

/**
 * Atualiza indicador de status do sistema
 */
function updateSystemStatus(running) {
    if (!elements.statusIndicator || !elements.statusText) return;
    
    if (running) {
        elements.statusIndicator.className = 'status-indicator running';
        elements.statusText.textContent = 'SISTEMA RODANDO';
        elements.btnStart.disabled = true;
        elements.btnStop.disabled = false;
        elements.btnCycle.disabled = true;
    } else {
        elements.statusIndicator.className = 'status-indicator stopped';
        elements.statusText.textContent = 'SISTEMA PARADO';
        elements.btnStart.disabled = false;
        elements.btnStop.disabled = true;
        elements.btnCycle.disabled = false;
    }
}

/**
 * Carrega informações do modelo de ML
 */
async function loadModelInfo() {
    try {
        const response = await fetch('/api/model/info');
        const data = await response.json();
        
        if (elements.modelTrained) {
            elements.modelTrained.textContent = data.model_trained ? 'SIM' : 'NÃO';
            elements.modelTrained.style.color = data.model_trained ? 'var(--success)' : 'var(--primary-cyan)';
        }
        
        if (elements.trainingSamples) {
            elements.trainingSamples.textContent = formatNumber(data.training_samples || 0);
        }
        
        if (elements.mlIndicator) {
            const span = elements.mlIndicator.querySelector('span');
            if (data.model_trained) {
                span.textContent = 'MODELO ATIVO';
                elements.mlIndicator.style.borderColor = 'var(--success)';
            } else if (data.training_samples > 0) {
                span.textContent = 'APRENDENDO...';
                elements.mlIndicator.style.borderColor = 'var(--warning)';
            } else {
                span.textContent = 'AGUARDANDO DADOS';
                elements.mlIndicator.style.borderColor = 'var(--primary-purple)';
            }
        }
    } catch (error) {
        console.error('Erro ao carregar info do modelo:', error);
    }
}

/**
 * Carrega lista de proxies ativos
 */
async function loadActiveProxies() {
    try {
        const response = await fetch('/api/proxies/active?limit=50');
        const data = await response.json();
        
        if (elements.proxyCount) {
            elements.proxyCount.textContent = data.count || 0;
        }
        
        if (elements.proxiesList) {
            if (data.proxies && data.proxies.length > 0) {
                renderProxiesList(data.proxies);
            } else {
                elements.proxiesList.innerHTML = `
                    <div class="no-proxies">
                        <div class="no-proxies-icon">◈</div>
                        <p>Nenhum proxy ativo encontrado</p>
                        <p class="hint">Inicie o sistema para coletar proxies</p>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar proxies:', error);
    }
}

/**
 * Renderiza lista de proxies
 */
function renderProxiesList(proxies) {
    if (!elements.proxiesList) return;
    
    elements.proxiesList.innerHTML = proxies.map(proxy => `
        <div class="proxy-item">
            <span class="proxy-address">${proxy}</span>
            <div class="proxy-info">
                <span>✓ VERIFICADO</span>
            </div>
        </div>
    `).join('');
}

/**
 * Inicia o sistema
 */
async function startSystem() {
    try {
        addLog('Iniciando sistema...', 'info');
        
        const response = await fetch('/api/system/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addLog(data.message, 'success');
            updateSystemStatus(true);
        } else {
            addLog(`Erro: ${data.detail || data.message}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao iniciar sistema:', error);
        addLog('Erro ao iniciar sistema', 'error');
    }
}

/**
 * Para o sistema
 */
async function stopSystem() {
    try {
        addLog('Parando sistema...', 'warning');
        
        const response = await fetch('/api/system/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addLog(data.message, 'info');
            updateSystemStatus(false);
        } else {
            addLog(`Erro: ${data.detail || data.message}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao parar sistema:', error);
        addLog('Erro ao parar sistema', 'error');
    }
}

/**
 * Executa um único ciclo
 */
async function runSingleCycle() {
    try {
        addLog('Executando ciclo único...', 'info');
        
        const response = await fetch('/api/system/cycle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addLog(data.message, 'info');
        } else {
            addLog(`Erro: ${data.detail || data.message}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao executar ciclo:', error);
        addLog('Erro ao executar ciclo', 'error');
    }
}

/**
 * Baixa lista de proxies
 */
function downloadProxies() {
    window.location.href = '/api/download/proxies';
    addLog('Download de proxies iniciado', 'info');
}

/**
 * Adiciona entrada ao log
 */
function addLog(message, type = 'info') {
    if (!elements.logContainer) return;
    
    const now = new Date();
    const timeStr = now.toLocaleTimeString('pt-BR', { hour12: false });
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
        <span class="log-time">${timeStr}</span>
        <span class="log-message">${message}</span>
    `;
    
    elements.logContainer.appendChild(logEntry);
    
    // Scroll para o final
    elements.logContainer.scrollTop = elements.logContainer.scrollHeight;
    
    // Manter apenas últimas 100 entradas
    const entries = elements.logContainer.querySelectorAll('.log-entry');
    if (entries.length > 100) {
        entries[0].remove();
    }
}

/**
 * Formata números grandes
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Inicia atualização automática
 */
function startAutoUpdate() {
    // Atualizar status a cada 5 segundos
    updateInterval = setInterval(() => {
        loadStatus();
        loadActiveProxies();
    }, 5000);
}

/**
 * Para atualização automática
 */
function stopAutoUpdate() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// Limpeza ao fechar página
window.addEventListener('beforeunload', () => {
    stopAutoUpdate();
    if (ws) {
        ws.close();
    }
});
