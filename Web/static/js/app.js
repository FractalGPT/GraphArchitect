// Хранилище загруженных файлов
let uploadedFiles = [];

// Обработка загрузки файлов
document.getElementById('file-input').addEventListener('change', async function(e) {
    const files = e.target.files;
    if (!files.length) return;

    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    try {
        const response = await fetch('/upload-files', {
            method: 'POST',
            body: formData
        });

        const html = await response.text();
        document.getElementById('file-display').innerHTML = html;

        // Сохраняем информацию о файлах
        uploadedFiles = Array.from(files).map(file => ({
            name: file.name,
            size: file.size,
            icon: getFileIcon(file.name)
        }));

        document.getElementById('files-data').value = JSON.stringify(uploadedFiles);
    } catch (error) {
        console.error('Error uploading files:', error);
    }
});

// Глобальная переменная для хранения цепочки агентов
let workflowAgents = [];

// Обработка отправки формы с потоковым выводом
document.getElementById('chat-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const message = document.getElementById('message-input').value.trim();
    if (!message) return;

    const chatMessages = document.getElementById('chat-messages');
    
    // Добавление пользовательского сообщения
    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.innerHTML = `<div class="message-content">${escapeHtml(message)}</div>`;
    chatMessages.appendChild(userMessage);

    // Скрыть welcome message
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.style.display = 'none';
    }

    // Создаем контейнер для ответа ассистента
    const assistantMessage = document.createElement('div');
    assistantMessage.id = 'streaming-message';
    chatMessages.appendChild(assistantMessage);

    // Отправка запроса с потоковым получением
    const formData = new FormData();
    formData.append('message', message);
    formData.append('files', document.getElementById('files-data').value);

    try {
        const response = await fetch('/chat/stream', {
            method: 'POST',
            body: formData
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let activeAgent = null;
        const completedAgents = [];
        let buffer = '';

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, {stream: true});
            buffer += chunk;
            
            // Проверяем метаданные workflow
            const workflowMatch = buffer.match(/<span data-workflow-agents='([^']+)' style="display:none;"><\/span>/);
            if (workflowMatch) {
                try {
                    const workflowData = JSON.parse(workflowMatch[1]);
                    workflowAgents = workflowData.agents || workflowData;
                    initializeWorkflow(workflowAgents);
                    buffer = buffer.replace(workflowMatch[0], '');
                } catch (e) {
                    console.error('Error parsing workflow agents:', e, workflowMatch[1]);
                }
            }
            
            // Проверяем маркеры начала работы агента
            let startMatch;
            while ((startMatch = buffer.match(/<span data-agent-start="(\d+)" style="display:none;"><\/span>/))) {
                activeAgent = parseInt(startMatch[1]);
                updateWorkflow(activeAgent, completedAgents);
                buffer = buffer.replace(startMatch[0], '');
            }
            
            // Проверяем маркеры завершения работы агента
            let completeMatch;
            while ((completeMatch = buffer.match(/<span data-agent-complete="(\d+)" style="display:none;"><\/span>/))) {
                const completedId = parseInt(completeMatch[1]);
                completedAgents.push(completedId);
                activeAgent = null;
                updateWorkflow(activeAgent, completedAgents);
                buffer = buffer.replace(completeMatch[0], '');
            }

            // Добавляем оставшийся контент к сообщению
            if (buffer) {
                assistantMessage.innerHTML += buffer;
                buffer = '';
            }

            // Автоскролл
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    } catch (error) {
        console.error('Ошибка при получении потокового ответа:', error);
        assistantMessage.innerHTML += '<br><span style="color: red;">Ошибка при получении ответа</span>';
    }

    // Очистка формы
    document.getElementById('message-input').value = '';
    document.getElementById('file-input').value = '';
    document.getElementById('file-display').innerHTML = '';
    document.getElementById('files-data').value = '';
    uploadedFiles = [];
    assistantMessage.id = '';
});

// Auto-resize textarea
document.getElementById('message-input').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// Enter для отправки, Shift+Enter для новой строки
document.getElementById('message-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('chat-form').dispatchEvent(new Event('submit'));
    }
});

// Вспомогательные функции
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📕',
        'doc': '📘', 'docx': '📘',
        'txt': '📄',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
        'mp3': '🎵', 'wav': '🎵', 'm4a': '🎵',
        'zip': '🗜️', 'rar': '🗜️', '7z': '🗜️'
    };
    return icons[ext] || '📎';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Инициализация workflow панели
function initializeWorkflow(agents) {
    if (!agents || agents.length === 0) {
        console.error('No agents provided to initializeWorkflow');
        return;
    }
    
    console.log('Initializing workflow with agents:', agents);
    
    const workflowSection = document.getElementById('workflow-display');
    const workflowSteps = document.querySelector('.workflow-steps');
    
    if (!workflowSection || !workflowSteps) {
        console.error('Workflow elements not found');
        return;
    }
    
    // Очищаем текущие шаги
    workflowSteps.innerHTML = '';
    
    // Создаем карточки для каждого агента
    agents.forEach((agent, index) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'workflow-step';
        
        const arrow = index < agents.length - 1 ? 
            '<div class="step-arrow">›</div>' : '';
        
        stepDiv.innerHTML = `
            <div class="step-card" data-agent-id="${agent.id}">
                <div class="step-icon">${agent.icon}</div>
                <div class="step-name">${agent.name}</div>
                <div class="step-status">Ожидание</div>
            </div>
            ${arrow}
        `;
        
        workflowSteps.appendChild(stepDiv);
    });
    
    // Показываем workflow панель с анимацией
    workflowSection.style.display = 'block';
    workflowSection.style.animation = 'slideInFromTop 0.5s ease-out';
    
    console.log('Workflow initialized with', agents.length, 'agents');
}

// Обновление workflow визуализации
function updateWorkflow(activeAgentId, completedAgentIds) {
    // Находим все карточки агентов
    const workflowSteps = document.querySelectorAll('.workflow-step');
    
    workflowSteps.forEach((step) => {
        const stepCard = step.querySelector('.step-card');
        const stepStatus = step.querySelector('.step-status');
        
        if (!stepCard || !stepStatus) return;
        
        const agentId = parseInt(stepCard.getAttribute('data-agent-id'));
        
        // Убираем все классы
        stepCard.classList.remove('active', 'completed');
        
        if (completedAgentIds.includes(agentId)) {
            // Завершено
            stepCard.classList.add('completed');
            stepStatus.textContent = 'Завершено';
        } else if (activeAgentId === agentId) {
            // В процессе
            stepCard.classList.add('active');
            stepStatus.textContent = 'Обработка...';
        } else {
            // Ожидание
            stepStatus.textContent = 'Ожидание';
        }
    });
}

// Workflow панель показывается только после получения данных от бэкенда