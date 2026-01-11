// === Workflow Visualizer Application ===
// WebSocket connection and UI management

class WorkflowVisualizer {
    constructor() {
        this.socket = null;
        this.currentWorkflow = null;
        this.currentStepIndex = 0;
        this.startTime = null;
        this.timerInterval = null;
        this.agentsLibrary = {};
        
        this.currentExecutionBlock = null;
        this.currentExecutionContent = null;
        this.isWorkflowFinished = false;
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Workflow Visualizer');
        this.connectWebSocket();
        this.loadAgentLibrary();
        this.setupEventListeners();
    }
    
    connectWebSocket() {
        this.socket = io({
            path: '/socket.io',
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 10
        });
        
        this.socket.on('connect', () => {
            console.log('✅ WebSocket connected!');
            document.getElementById('stat-status').textContent = 'Connected';
        });
        
        this.socket.on('workflow_info', (data) => this.onWorkflowInfo(data));
        this.socket.on('step_started', (data) => this.onStepStarted(data));
        this.socket.on('agent_progress', (data) => this.onAgentProgress(data));
        this.socket.on('agent_score_updated', (data) => this.onAgentScoreUpdated(data));
        this.socket.on('agent_selected', (data) => this.onAgentSelected(data));
        this.socket.on('agent_executing', (data) => this.onAgentExecuting(data));
        this.socket.on('step_completed', (data) => this.onStepCompleted(data));
        this.socket.on('workflow_completed', (data) => this.onWorkflowCompleted(data));
        this.socket.on('workflow_stopped', (data) => this.onWorkflowStopped(data));
        this.socket.on('workflow_error', (data) => this.onWorkflowError(data));
    }
    
    async loadAgentLibrary() {
        try {
            const response = await fetch('/api/agents-library');
            const data = await response.json();
            data.agents.forEach(agent => this.agentsLibrary[agent.id] = agent);
            this.renderAgentLibrary(data.agents);
        } catch (error) {
            console.error('Error loading agents:', error);
        }
    }
    
    setupEventListeners() {
        document.getElementById('template-selector').addEventListener('change', (e) => {
            document.getElementById('start-btn').disabled = !e.target.value;
        });
        
        document.getElementById('start-btn').addEventListener('click', () => this.startWorkflow());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopWorkflow());
        document.getElementById('agent-search').addEventListener('input', (e) => this.filterAgentLibrary(e.target.value));
    }
    
    // === Workflow Control ===
    
    startWorkflow(customTemplate = null) {
        const template = customTemplate || document.getElementById('template-selector').value;
        if (!template) return;
        
        document.getElementById('welcome-message').style.display = 'none';
        
        this.socket.emit('start_workflow', {
            template: template,
            chat_id: `wf_${Date.now()}`
        });
        
        this.startTime = Date.now();
        this.startTimer();
        this.isWorkflowFinished = false;
        
        document.getElementById('start-btn').disabled = true;
        document.getElementById('stop-btn').disabled = false;
        document.getElementById('stat-status').textContent = 'Running';
    }

    startWorkflowFromChat(message) {
        this.addUserMessage(message);
        
        let template = 'customer_support';
        if (message.toLowerCase().includes('код')) template = 'code_review';
        if (message.toLowerCase().includes('текст') || message.toLowerCase().includes('стать')) template = 'content_creation';
        
        this.startWorkflow(template);
    }

    addUserMessage(text) {
        const chatMessages = document.getElementById('chat-messages');
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message user-message';
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    addAssistantMessage(text, agentName = "Архитектор") {
        const chatMessages = document.getElementById('chat-messages');
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant-message';
        msgDiv.innerHTML = `<strong>${agentName}:</strong><br>${text}`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    stopWorkflow() {
        if (this.currentWorkflow) {
            this.socket.emit('stop_workflow', { workflow_id: this.currentWorkflow.workflowId });
            this.stopTimer();
            this.resetUI();
        }
    }
    
    // === Logging & Collapsible Blocks ===
    
    addLog(type, message) {
        if (!this.currentExecutionBlock || this.isWorkflowFinished) {
            this.createNewExecutionBlock();
        }

        const logEntry = document.createElement('div');
        logEntry.style.padding = '4px 0';
        logEntry.style.borderBottom = '1px solid #f1f1f1';
        
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
        logEntry.innerHTML = `<span style="color: #adb5bd; margin-right: 8px;">[${time}]</span> <span>${message}</span>`;
        
        this.currentExecutionContent.appendChild(logEntry);
        this.currentExecutionContent.scrollTop = this.currentExecutionContent.scrollHeight;
        
        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
    }

    createNewExecutionBlock() {
        const chatMessages = document.getElementById('chat-messages');
        const block = document.createElement('div');
        block.className = 'execution-block';
        
        block.innerHTML = `
            <div class="execution-header">
                <span class="exec-title" style="font-weight: 600;">⚙️ Выполнение графа агентов...</span>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="execution-content"></div>
        `;
        
        chatMessages.appendChild(block);
        this.currentExecutionBlock = block;
        this.currentExecutionContent = block.querySelector('.execution-content');
        this.isWorkflowFinished = false;
        
        block.querySelector('.execution-header').onclick = () => {
            block.classList.toggle('collapsed');
            const icon = block.querySelector('.toggle-icon');
            icon.textContent = block.classList.contains('collapsed') ? '►' : '▼';
        };
    }

    // === WebSocket Event Handlers ===
    
    onWorkflowInfo(data) {
        this.currentWorkflow = data;
        this.renderWorkflowSteps(data.steps);
        this.addLog('info', `✅ Сгенерирован граф: ${data.name}`);
    }
    
    onStepStarted(data) {
        this.currentStepIndex = data.stepIndex;
        this.updateStepStatus(data.stepIndex, 'in-progress');
        document.getElementById('current-step-name').textContent = data.stepName;
        document.getElementById('stat-current-step').textContent = `${data.stepIndex + 1}/${this.currentWorkflow.steps.length}`;
        
        document.getElementById('competing-agents').innerHTML = '';
        data.candidateAgents.forEach(agentId => {
            const agent = this.agentsLibrary[agentId];
            if (agent) this.addCompetingAgent(agent);
        });
        
        this.addLog('info', `📍 Шаг: ${data.stepName}`);
    }
    
    onAgentProgress(data) {
        const agentCard = document.querySelector(`[data-agent-id="${data.agentId}"]`);
        if (agentCard && !agentCard.classList.contains('winner')) {
            agentCard.querySelector('.progress-bar').style.width = `${data.progress}%`;
            agentCard.querySelector('.progress-text').textContent = `${data.progress}%`;
        }
    }
    
    onAgentScoreUpdated(data) {
        const agentCard = document.querySelector(`[data-agent-id="${data.agentId}"]`);
        if (agentCard) {
            const scoreValue = agentCard.querySelector('.metric-value.score');
            if (scoreValue) scoreValue.textContent = (data.score * 100).toFixed(0) + '%';
        }
        this.updateLeader(data.agents);
    }
    
    updateLeader(agents) {
        document.querySelectorAll('.agent-competing-card').forEach(card => {
            if (!card.classList.contains('winner')) {
                card.classList.remove('leading');
            }
        });
        let leader = null;
        let maxScore = -1;
        agents.forEach(agent => {
            if (agent.score !== null && agent.score > maxScore) {
                maxScore = agent.score;
                leader = agent.agentId;
            }
        });
        if (leader) {
            const leaderCard = document.querySelector(`[data-agent-id="${leader}"]`);
            if (leaderCard && !leaderCard.classList.contains('winner')) {
                leaderCard.classList.add('leading');
            }
        }
    }
    
    onAgentSelected(data) {
        const winner = this.agentsLibrary[data.winnerId];
        this.addLog('success', `🎯 Выбран агент: ${winner.name} (${(data.score * 100).toFixed(0)}%)`);
        
        document.querySelectorAll('.agent-competing-card').forEach(card => {
            const cardId = card.getAttribute('data-agent-id');
            card.classList.remove('competing', 'leading');
            
            if (cardId === data.winnerId) {
                card.classList.add('winner');
                const badge = card.querySelector('.agent-status-badge');
                if (badge) {
                    badge.textContent = '⚙️ Executing';
                    badge.className = 'agent-status-badge winner';
                }
                // СБРОС ПРОГРЕССА ДЛЯ "ВТОРОГО ПРОХОДА"
                const progressBar = card.querySelector('.progress-bar');
                const progressText = card.querySelector('.progress-text');
                if (progressBar) progressBar.style.width = '0%';
                if (progressText) progressText.textContent = '0%';
            } else {
                card.classList.add('eliminated');
                const badge = card.querySelector('.agent-status-badge');
                if (badge) badge.textContent = 'Eliminated';
            }
        });
        
        // Удаляем проигравших через 1.5 секунды
        setTimeout(() => {
            document.querySelectorAll('.agent-competing-card.eliminated').forEach(card => {
                card.style.display = 'none';
            });
        }, 1500);
    }
    
    onAgentExecuting(data) {
        const agentCard = document.querySelector(`[data-agent-id="${data.agentId}"]`);
        if (agentCard && agentCard.classList.contains('winner')) {
            const progressBar = agentCard.querySelector('.progress-bar');
            const progressText = agentCard.querySelector('.progress-text');
            
            if (progressBar) progressBar.style.width = `${data.progress}%`;
            if (progressText) progressText.textContent = `${data.progress}%`;
            
            let actionLog = agentCard.querySelector('.agent-action-log');
            if (!actionLog) {
                actionLog = document.createElement('div');
                actionLog.className = 'agent-action-log';
                actionLog.style.fontSize = '11px';
                actionLog.style.color = '#4c6ef5';
                actionLog.style.marginTop = '8px';
                actionLog.style.fontWeight = '600';
                agentCard.querySelector('.agent-progress').appendChild(actionLog);
            }
            actionLog.textContent = `▶ ${data.action}`;
        }
        
        if (data.progress === 100) {
            this.addLog('success', `✨ ${this.agentsLibrary[data.agentId].name}: ${data.action}`);
        }
    }
    
    onStepCompleted(data) {
        this.updateStepStatus(this.currentStepIndex, 'completed');
        const progress = Math.round(((this.currentStepIndex + 1) / this.currentWorkflow.steps.length) * 100);
        document.getElementById('stat-progress').textContent = `${progress}%`;
        document.getElementById('stat-progress-fill').style.width = `${progress}%`;
    }
    
    onWorkflowCompleted(data) {
        console.log('🎉 Workflow completed');
        this.addLog('success', '🎉 Workflow успешно завершен!');
        
        this.stopTimer();
        this.isWorkflowFinished = true;
        
        if (data.finalAnswer) {
            setTimeout(() => {
                this.addAssistantMessage(data.finalAnswer, "Графовый Архитектор");
            }, 500);
        }
        
        setTimeout(() => {
            if (this.currentExecutionBlock) {
                this.currentExecutionBlock.classList.add('collapsed');
                const title = this.currentExecutionBlock.querySelector('.exec-title');
                const icon = this.currentExecutionBlock.querySelector('.toggle-icon');
                if (title) title.textContent = '📑 Детали выполнения графа (нажмите для просмотра)';
                if (icon) icon.textContent = '►';
            }
        }, 1500);
        
        document.getElementById('stat-status').textContent = 'Finished';
    }
    
    onWorkflowStopped() {
        this.addLog('warning', '⏹ Граф остановлен');
        this.resetUI();
    }
    
    onWorkflowError(data) {
        this.addLog('error', `❌ Ошибка: ${data.error}`);
        this.resetUI();
    }
    
    // === UI Rendering ===
    
    renderWorkflowSteps(steps) {
        const container = document.getElementById('workflow-steps');
        container.innerHTML = '';
        steps.forEach((step, index) => {
            const stepItem = document.createElement('div');
            stepItem.className = 'step-item';
            stepItem.setAttribute('data-step-index', index);
            stepItem.innerHTML = `<div class="step-card pending"><div class="step-name">${step.name}</div><div class="step-status">⏳</div></div>`;
            container.appendChild(stepItem);
            if (index < steps.length - 1) {
                const arrow = document.createElement('div');
                arrow.className = 'step-arrow';
                arrow.textContent = '→';
                container.appendChild(arrow);
            }
        });
    }
    
    updateStepStatus(stepIndex, status) {
        const stepItem = document.querySelector(`[data-step-index="${stepIndex}"]`);
        if (!stepItem) return;
        const card = stepItem.querySelector('.step-card');
        card.classList.remove('pending', 'in-progress', 'completed');
        card.classList.add(status);
        stepItem.querySelector('.step-status').textContent = status === 'in-progress' ? '⚡' : (status === 'completed' ? '✅' : '⏳');
    }
    
    addCompetingAgent(agent) {
        const container = document.getElementById('competing-agents');
        const card = document.createElement('div');
        card.className = 'agent-competing-card competing';
        card.setAttribute('data-agent-id', agent.id);
        const cost = agent.cost || 0;
        const quality = Math.round((agent.metrics?.avgScore || 0) * 100);
        const time = agent.metrics?.avgResponseTime || 0;
        card.innerHTML = `
            <div class="agent-card-header">
                <div class="agent-avatar" style="background: ${agent.color}20; color: ${agent.color}">${agent.icon}</div>
                <div class="agent-info-text">
                    <h4>${agent.name}</h4>
                    <div class="agent-badges-row">
                        <span class="badge-cost">$${cost.toFixed(3)}</span>
                        <span class="badge-quality">🏆 ${quality}%</span>
                        <span class="badge-time">⏱️ ${time}ms</span>
                    </div>
                </div>
                <div class="agent-status-badge competing">Competing</div>
            </div>
            <div class="agent-progress">
                <div class="progress-bar-container"><div class="progress-bar" style="width: 0%"></div></div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                    <span style="font-size: 10px; color: #868e96;">Progress</span>
                    <span class="progress-text" style="font-size: 10px; font-weight: 700; color: #4c6ef5;">0%</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    }
    
    renderAgentLibrary(agents) {
        const container = document.getElementById('agent-library');
        container.innerHTML = '';
        agents.forEach(agent => {
            const card = document.createElement('div');
            card.className = 'library-agent-card';
            const cost = agent.cost || 0;
            const quality = Math.round((agent.metrics?.avgScore || 0) * 100);
            card.innerHTML = `
                <div class="library-agent-avatar" style="background: ${agent.color}20; color: ${agent.color}">${agent.icon}</div>
                <div class="library-agent-info">
                    <h5>${agent.name}</h5>
                    <div class="agent-badges-row">
                        <span class="badge-cost">$${cost.toFixed(3)}</span>
                        <span class="badge-quality">🏆 ${quality}%</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    }
    
    filterAgentLibrary(term) {
        document.querySelectorAll('.library-agent-card').forEach(card => {
            const name = card.querySelector('h5').textContent.toLowerCase();
            card.style.display = name.includes(term.toLowerCase()) ? 'flex' : 'none';
        });
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const s = Math.floor(elapsed / 1000);
            document.getElementById('stat-time').textContent = `${Math.floor(s/60)}:${(s%60).toString().padStart(2,'0')}`;
        }, 1000);
    }
    
    stopTimer() { clearInterval(this.timerInterval); }
    
    resetUI() {
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;
        document.getElementById('stat-status').textContent = 'Готов';
        document.getElementById('stat-progress').textContent = '0%';
        document.getElementById('stat-progress-fill').style.width = '0%';
        document.getElementById('competing-agents').innerHTML = '<div class="no-agents-message">Агенты появятся при работе шага</div>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.workflowApp = new WorkflowVisualizer();
});
