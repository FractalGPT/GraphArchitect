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

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, {stream: true});
            
            // Добавляем chunk к сообщению
            assistantMessage.innerHTML += chunk;
            
            // Проверяем маркеры агентов
            const startMatch = chunk.match(/data-agent-start="(\d+)"/);
            if (startMatch) {
                activeAgent = parseInt(startMatch[1]);
                updateWorkflow(activeAgent, completedAgents);
            }
            
            const completeMatch = chunk.match(/data-agent-complete="(\d+)"/);
            if (completeMatch) {
                const completedId = parseInt(completeMatch[1]);
                completedAgents.push(completedId);
                activeAgent = null;
                updateWorkflow(activeAgent, completedAgents);
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

// Обновление workflow визуализации
function updateWorkflow(activeAgentId, completedAgentIds) {
    const agents = [
        {id: 1, name: 'Researcher', icon: '🔍'},
        {id: 2, name: 'Analyzer', icon: '📊'},
        {id: 3, name: 'Writer', icon: '✍️'},
        {id: 4, name: 'Reviewer', icon: '✅'}
    ];
    
    // Находим все карточки агентов
    const workflowSteps = document.querySelectorAll('.workflow-step');
    
    agents.forEach((agent, index) => {
        if (index >= workflowSteps.length) return;
        
        const stepCard = workflowSteps[index].querySelector('.step-card');
        const stepStatus = workflowSteps[index].querySelector('.step-status');
        
        if (!stepCard || !stepStatus) return;
        
        // Убираем все классы
        stepCard.classList.remove('active', 'completed');
        
        if (completedAgentIds.includes(agent.id)) {
            // Завершено
            stepCard.classList.add('completed');
            stepStatus.textContent = 'Завершено';
        } else if (activeAgentId === agent.id) {
            // В процессе
            stepCard.classList.add('active');
            stepStatus.textContent = 'Обработка...';
        } else {
            // Ожидание
            stepStatus.textContent = 'Ожидание';
        }
    });
}