// === Main Chat Application ===
// Integration with WorkflowVisualizer

document.getElementById('chat-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    if (!message) return;

    // Скрываем приветствие
    const welcome = document.getElementById('welcome-message');
    if (welcome) welcome.style.display = 'none';

    // Очищаем ввод
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Если подключен WorkflowVisualizer, запускаем его через сообщение чата
    if (window.workflowApp) {
        window.workflowApp.startWorkflowFromChat(message);
    }
});

// Обработка загрузки файлов
document.getElementById('file-input').addEventListener('change', async function(e) {
    const files = e.target.files;
    if (!files.length) return;

    const fileDisplay = document.getElementById('file-display');
    
    for (let file of files) {
        const chip = document.createElement('div');
        chip.className = 'file-chip';
        chip.innerHTML = `<span>📎</span> <span>${file.name}</span>`;
        fileDisplay.appendChild(chip);
    }
});

// Auto-resize textarea
document.getElementById('message-input').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// Enter для отправки
document.getElementById('message-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('chat-form').dispatchEvent(new Event('submit'));
    }
});
