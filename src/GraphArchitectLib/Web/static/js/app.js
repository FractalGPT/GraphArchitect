// === Main Chat Application ===
// Integration with WorkflowVisualizer

// Хранилище для загруженных файлов
let uploadedFileIds = [];

// Обработка клика на кнопку (для режима Стоп)
document.getElementById('send-btn').addEventListener('click', function(e) {
    if (this.type === 'button') {
        if (window.workflowApp) window.workflowApp.stopWorkflow();
    }
});

document.getElementById('chat-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Если кнопка в режиме Стоп, выходим (обработано выше)
    const sendBtn = document.getElementById('send-btn');
    if (sendBtn.type === 'button') return;
    
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    if (!message && uploadedFileIds.length === 0) return;

    // Скрываем приветствие
    const welcome = document.getElementById('welcome-message');
    if (welcome) welcome.style.display = 'none';

    // Очищаем ввод
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Если подключен WorkflowVisualizer, запускаем его через сообщение чата
    if (window.workflowApp) {
        window.workflowApp.startWorkflowFromChat(message, [...uploadedFileIds]);
    }

    // Очищаем файлы после отправки
    clearFiles();
});

// Обработка загрузки файлов
document.getElementById('file-input').addEventListener('change', async function(e) {
    const files = e.target.files;
    if (!files.length) return;

    for (let file of files) {
        await uploadFile(file);
    }
    
    // Сбрасываем input чтобы можно было выбрать тот же файл снова
    this.value = '';
});

async function uploadFile(file) {
    const fileDisplay = document.getElementById('file-display');
    
    // Создаем временный чип с индикатором загрузки
    const chip = document.createElement('div');
    chip.className = 'file-chip loading';
    chip.innerHTML = `<span>⏳</span> <span>${file.name}</span>`;
    fileDisplay.appendChild(chip);

    try {
        const formData = new FormData();
        formData.append('file', file);

        // Используем эндпоинт из api_router.py
        // Так как chat_id еще может не быть, генерируем временный
        const tempChatId = `chat_${Date.now()}`;
        const response = await fetch(`/api/chat/${tempChatId}/document`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();
        
        // Обновляем чип
        chip.classList.remove('loading');
        chip.innerHTML = `
            <span>📎</span> 
            <span class="file-name">${file.name}</span>
            <button class="remove-file" data-id="${data.document_id}">✕</button>
        `;
        
        uploadedFileIds.push(data.document_id);

        // Добавляем обработчик удаления
        chip.querySelector('.remove-file').onclick = () => {
            uploadedFileIds = uploadedFileIds.filter(id => id !== data.document_id);
            chip.remove();
        };

    } catch (error) {
        console.error('Error uploading file:', error);
        chip.innerHTML = `<span>❌</span> <span>${file.name} (Ошибка)</span>`;
        setTimeout(() => chip.remove(), 3000);
    }
}

function clearFiles() {
    uploadedFileIds = [];
    document.getElementById('file-display').innerHTML = '';
}

// Drag & Drop
const dropZone = document.querySelector('.input-wrapper');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
});

dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) {
        for (let file of files) {
            uploadFile(file);
        }
    }
}, false);

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
