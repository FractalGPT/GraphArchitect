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
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Workflow Visualizer');
        
        // Connect to Socket.IO
        this.connectWebSocket();
        
        // Load agent library
        this.loadAgentLibrary();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    connectWebSocket() {
        console.log('🔌 Connecting to WebSocket...');
        
        // Подключение к Socket.IO (на корневом уровне /socket.io/)
        this.socket = io({
            path: '/socket.io', // Убрал лишний слеш в конце для надежности
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 10,
            timeout: 20000
        });
        
        this.socket.on('connect', () => {
            console.log('✅ WebSocket connected! ID:', this.socket.id);
            this.addLog('success', '✅ Соединение с сервером установлено');
            document.getElementById('stat-status').textContent = 'Connected';
            document.getElementById('stat-status').className = 'stat-value status-completed';
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('❌ Connection error:', error);
            this.addLog('error', `❌ Ошибка подключения: ${error.message}`);
            document.getElementById('stat-status').textContent = 'Conn Error';
            document.getElementById('stat-status').className = 'stat-value status-idle';
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('❌ WebSocket disconnected:', reason);
            this.addLog('warning', `⚠️ Отключено от сервера: ${reason}`);
            this.stopTimer();
            this.resetUI();
        });
        
        // Workflow events
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
        this.socket.on('error', (data) => this.onError(data));
    }
    
    async loadAgentLibrary() {
        try {
            const response = await fetch('/api/agents-library');
            const data = await response.json();
            
            data.agents.forEach(agent => {
                this.agentsLibrary[agent.id] = agent;
            });
            
            this.renderAgentLibrary(data.agents);
            console.log(`📚 Loaded ${data.agents.length} agents`);
        } catch (error) {
            console.error('Error loading agents:', error);
        }
    }
    
    setupEventListeners() {
        // Template selector
        document.getElementById('template-selector').addEventListener('change', (e) => {
            const templateValue = e.target.value;
            document.getElementById('start-btn').disabled = !templateValue;
        });
        
        // Start button
        document.getElementById('start-btn').addEventListener('click', () => {
            this.startWorkflow();
        });
        
        // Stop button
        document.getElementById('stop-btn').addEventListener('click', () => {
            this.stopWorkflow();
        });
        
        // Clear logs
        document.getElementById('clear-logs-btn').addEventListener('click', () => {
            this.clearLogs();
        });
        
        // Agent search
        document.getElementById('agent-search').addEventListener('input', (e) => {
            this.filterAgentLibrary(e.target.value);
        });
    }
    
    // === Workflow Control ===
    
    startWorkflow() {
        const template = document.getElementById('template-selector').value;
        if (!template) return;
        
        console.log(`▶️ Starting workflow: ${template}`);
        this.addLog('info', `Запуск workflow: ${template}`);
        
        this.socket.emit('start_workflow', {
            template: template,
            chat_id: `workflow_${Date.now()}`
        });
        
        this.startTime = Date.now();
        this.startTimer();
        
        // UI updates
        document.getElementById('start-btn').disabled = true;
        document.getElementById('stop-btn').disabled = false;
        document.getElementById('template-selector').disabled = true;
        document.getElementById('stat-status').textContent = 'Running';
        document.getElementById('stat-status').className = 'stat-value status-running';
    }
    
    stopWorkflow() {
        if (this.currentWorkflow) {
            console.log('⏹️ Stopping workflow');
            this.socket.emit('stop_workflow', {
                workflow_id: this.currentWorkflow.workflowId
            });
            
            this.stopTimer();
            this.resetUI();
        }
    }
    
    // === WebSocket Event Handlers ===
    
    onWorkflowInfo(data) {
        console.log('📋 Workflow info received:', data);
        this.currentWorkflow = data;
        
        document.getElementById('workflow-name').textContent = data.name;
        document.getElementById('workflow-description').textContent = data.description;
        
        this.renderWorkflowSteps(data.steps);
        this.addLog('info', `Workflow создан: ${data.steps.length} шагов`);
    }
    
    onStepStarted(data) {
        console.log(`📍 Step started: ${data.stepName}`);
        this.currentStepIndex = data.stepIndex;
        
        // Update UI
        this.updateStepStatus(data.stepIndex, 'in-progress');
        document.getElementById('current-step-name').textContent = `Шаг ${data.stepIndex + 1}: ${data.stepName}`;
        document.getElementById('stat-current-step').textContent = `${data.stepIndex + 1}/${this.currentWorkflow.steps.length}`;
        
        // Clear competing agents panel
        document.getElementById('competing-agents').innerHTML = '';
        
        // Add candidate agents
        data.candidateAgents.forEach(agentId => {
            const agent = this.agentsLibrary[agentId];
            if (agent) {
                this.addCompetingAgent(agent);
            }
        });
        
        this.addLog('info', `Шаг ${data.stepIndex + 1}: ${data.stepName} - конкурс ${data.candidateAgents.length} агентов`);
    }
    
    onAgentProgress(data) {
        const agentCard = document.querySelector(`[data-agent-id="${data.agentId}"]`);
        if (agentCard) {
            const progressBar = agentCard.querySelector('.progress-bar');
            const progressText = agentCard.querySelector('.progress-text');
            
            if (progressBar) {
                progressBar.style.width = `${data.progress}%`;
            }
            if (progressText) {
                progressText.textContent = `${data.progress}%`;
            }
        }
    }
    
    onAgentScoreUpdated(data) {
        console.log(`⭐ Score updated for ${data.agentId}: ${data.score}`);
        
        const agentCard = document.querySelector(`[data-agent-id="${data.agentId}"]`);
        if (agentCard) {
            const scoreValue = agentCard.querySelector('.metric-value.score');
            if (scoreValue) {
                scoreValue.textContent = data.score.toFixed(3);
                
                // Flash animation
                agentCard.style.animation = 'none';
                setTimeout(() => {
                    agentCard.style.animation = '';
                }, 10);
            }
        }
        
        // Update leader
        this.updateLeader(data.agents);
    }
    
    updateLeader(agents) {
        // Remove all leader classes
        document.querySelectorAll('.agent-competing-card').forEach(card => {
            card.classList.remove('leading');
            const badge = card.querySelector('.agent-status-badge');
            if (badge && badge.classList.contains('leading')) {
                badge.className = 'agent-status-badge competing';
                badge.textContent = 'Competing';
            }
        });
        
        // Find leader (highest score)
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
            if (leaderCard) {
                leaderCard.classList.add('leading');
                const badge = leaderCard.querySelector('.agent-status-badge');
                if (badge) {
                    badge.className = 'agent-status-badge leading';
                    badge.textContent = '🏆 Leading';
                }
            }
        }
    }
    
    onAgentSelected(data) {
        console.log(`🎯 Winner selected: ${data.winnerId}`);
        this.addLog('success', `Победитель: ${this.agentsLibrary[data.winnerId]?.name} (score: ${data.score.toFixed(3)})`);
        
        // Mark winner
        document.querySelectorAll('.agent-competing-card').forEach(card => {
            const agentId = card.getAttribute('data-agent-id');
            
            if (agentId === data.winnerId) {
                card.classList.remove('competing', 'leading');
                card.classList.add('winner');
                const badge = card.querySelector('.agent-status-badge');
                if (badge) {
                    badge.className = 'agent-status-badge winner';
                    badge.textContent = '👑 Winner';
                }
            } else {
                card.classList.add('eliminated');
            }
        });
        
        // After animation, keep only winner
        setTimeout(() => {
            document.querySelectorAll('.agent-competing-card.eliminated').forEach(card => {
                card.remove();
            });
        }, 1500);
    }
    
    onAgentExecuting(data) {
        const agentCard = document.querySelector(`[data-agent-id="${data.agentId}"]`);
        if (agentCard) {
            // Update progress during execution
            const progressBar = agentCard.querySelector('.progress-bar');
            const progressText = agentCard.querySelector('.progress-text');
            
            if (progressBar) {
                progressBar.style.width = `${data.progress}%`;
            }
            if (progressText) {
                progressText.textContent = `${data.progress}%`;
            }
            
            // Add action log
            const actionLog = agentCard.querySelector('.agent-action-log');
            if (actionLog) {
                actionLog.textContent = data.action;
            } else {
                // Create action log element
                const logDiv = document.createElement('div');
                logDiv.className = 'agent-action-log';
                logDiv.style.fontSize = '11px';
                logDiv.style.color = '#666';
                logDiv.style.marginTop = '8px';
                logDiv.textContent = data.action;
                agentCard.querySelector('.agent-progress').appendChild(logDiv);
            }
        }
        
        if (data.progress === 100) {
            this.addLog('success', `${this.agentsLibrary[data.agentId]?.name}: ${data.action}`);
        }
    }
    
    onStepCompleted(data) {
        console.log(`✅ Step completed: ${data.stepId}`);
        this.updateStepStatus(this.currentStepIndex, 'completed');
        this.addLog('success', `Шаг ${this.currentStepIndex + 1} завершен`);
        
        // Update progress
        const progress = Math.round(((this.currentStepIndex + 1) / this.currentWorkflow.steps.length) * 100);
        document.getElementById('stat-progress').textContent = `${progress}%`;
    }
    
    onWorkflowCompleted(data) {
        console.log('🎉 Workflow completed');
        this.addLog('success', '🎉 Workflow успешно завершен!');
        
        this.stopTimer();
        
        document.getElementById('stat-status').textContent = 'Completed';
        document.getElementById('stat-status').className = 'stat-value status-completed';
        document.getElementById('stat-progress').textContent = '100%';
        
        // Reset buttons
        setTimeout(() => {
            this.resetUI();
        }, 3000);
    }
    
    onWorkflowStopped(data) {
        console.log('🛑 Workflow stopped');
        this.addLog('warning', '🛑 Workflow остановлен пользователем');
        
        this.stopTimer();
        this.resetUI();
        
        document.getElementById('stat-status').textContent = 'Stopped';
        document.getElementById('stat-status').className = 'stat-value status-idle';
    }
    
    onWorkflowError(data) {
        console.error('❌ Workflow error:', data);
        this.addLog('error', `❌ Ошибка workflow: ${data.error}`);
        
        this.stopTimer();
        
        document.getElementById('stat-status').textContent = 'Error';
        document.getElementById('stat-status').className = 'stat-value status-idle';
        
        // Reset buttons after error
        setTimeout(() => {
            this.resetUI();
        }, 3000);
    }
    
    onError(data) {
        console.error('Error:', data);
        this.addLog('error', `Ошибка: ${data.message}`);
    }
    
    // === UI Rendering ===
    
    renderWorkflowSteps(steps) {
        const container = document.getElementById('workflow-steps');
        container.innerHTML = '';
        
        steps.forEach((step, index) => {
            // Step card
            const stepItem = document.createElement('div');
            stepItem.className = 'step-item';
            stepItem.setAttribute('data-step-index', index);
            
            const stepCard = document.createElement('div');
            stepCard.className = 'step-card pending';
            stepCard.innerHTML = `
                <div class="step-number">${step.order}</div>
                <div class="step-name">${step.name}</div>
                <div class="step-desc">${step.description || ''}</div>
                <div class="step-status">⏳</div>
            `;
            
            stepItem.appendChild(stepCard);
            container.appendChild(stepItem);
            
            // Arrow between steps
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
        
        const stepCard = stepItem.querySelector('.step-card');
        const stepStatus = stepItem.querySelector('.step-status');
        
        // Remove all status classes
        stepCard.classList.remove('pending', 'in-progress', 'completed');
        stepCard.classList.add(status);
        
        // Update status icon
        if (status === 'in-progress') {
            stepStatus.textContent = '⚡';
            
            // Animate arrows
            const allArrows = document.querySelectorAll('.step-arrow');
            if (allArrows[stepIndex]) {
                allArrows[stepIndex].classList.add('active');
            }
        } else if (status === 'completed') {
            stepStatus.textContent = '✅';
        }
    }
    
    addCompetingAgent(agent) {
        const container = document.getElementById('competing-agents');
        
        const agentCard = document.createElement('div');
        agentCard.className = 'agent-competing-card competing';
        agentCard.setAttribute('data-agent-id', agent.id);
        
        agentCard.innerHTML = `
            <div class="agent-card-header">
                <div class="agent-avatar" style="background: ${agent.color}">
                    ${agent.icon}
                </div>
                <div class="agent-info-text">
                    <h4>${agent.name}</h4>
                    <p>${agent.specialization || agent.type}</p>
                </div>
                <div class="agent-status-badge competing">Competing</div>
            </div>
            <div class="agent-metrics">
                <div class="metric-item">
                    <span class="metric-label">⭐ Score:</span>
                    <span class="metric-value score">--</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">⚡ Speed:</span>
                    <span class="metric-value">${agent.metrics.avgResponseTime}ms</span>
                </div>
            </div>
            <div class="agent-progress">
                <div class="agent-progress-label">
                    <span>Progress</span>
                    <span class="progress-text">0%</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: 0%"></div>
                </div>
            </div>
        `;
        
        container.appendChild(agentCard);
    }
    
    renderAgentLibrary(agents) {
        const container = document.getElementById('agent-library');
        container.innerHTML = '';
        
        agents.forEach(agent => {
            const card = document.createElement('div');
            card.className = 'library-agent-card';
            card.setAttribute('data-agent-id', agent.id);
            card.setAttribute('data-agent-name', agent.name.toLowerCase());
            card.setAttribute('data-agent-type', agent.type.toLowerCase());
            
            card.innerHTML = `
                <div class="library-agent-header">
                    <div class="library-agent-avatar" style="background: ${agent.color}">
                        ${agent.icon}
                    </div>
                    <div class="library-agent-info">
                        <h5>${agent.name}</h5>
                        <p>${agent.specialization}</p>
                    </div>
                </div>
                <div class="library-agent-type">${agent.type}</div>
            `;
            
            container.appendChild(card);
        });
    }
    
    filterAgentLibrary(searchTerm) {
        const term = searchTerm.toLowerCase();
        const cards = document.querySelectorAll('.library-agent-card');
        
        cards.forEach(card => {
            const name = card.getAttribute('data-agent-name');
            const type = card.getAttribute('data-agent-type');
            
            if (name.includes(term) || type.includes(term)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    // === Logging ===
    
    addLog(type, message) {
        const logsContainer = document.getElementById('execution-logs');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        
        const time = new Date().toLocaleTimeString();
        logEntry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-message">${message}</span>
        `;
        
        logsContainer.appendChild(logEntry);
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }
    
    clearLogs() {
        document.getElementById('execution-logs').innerHTML = '';
        this.addLog('info', 'Логи очищены');
    }
    
    // === Timer ===
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const seconds = Math.floor(elapsed / 1000);
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            
            document.getElementById('stat-time').textContent = 
                `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
    
    // === UI Reset ===
    
    resetUI() {
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;
        document.getElementById('template-selector').disabled = false;
        document.getElementById('stat-status').textContent = 'Idle';
        document.getElementById('stat-status').className = 'stat-value status-idle';
        document.getElementById('current-step-name').textContent = 'Ожидание начала...';
        document.getElementById('competing-agents').innerHTML = `
            <div class="no-agents-message">
                <p>Выберите и запустите workflow для начала конкурентного выбора агентов</p>
            </div>
        `;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new WorkflowVisualizer();
    window.workflowApp = app; // Expose for debugging
});
