const API_BASE_URL = 'http://127.0.0.1:8000';

const messagesEl = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const fileInput = document.getElementById('fileInput');

function addMessage(text, sender = 'user', options = {}) {
  const { imageUrl, isRouting = false } = options;

  if (isRouting) {
    const routingDiv = document.createElement('div');
    routingDiv.classList.add('routing-message');
    routingDiv.textContent = text;
    messagesEl.appendChild(routingDiv);
    scrollToBottom();
    return;
  }

  const messageDiv = document.createElement('div');
  messageDiv.classList.add('message', `${sender}-message`);

  const contentDiv = document.createElement('div');
  contentDiv.classList.add('message-content');

  if (imageUrl) {
    const img = document.createElement('img');
    img.src = imageUrl;
    img.classList.add('message-image');
    img.alt = 'Медицинское изображение';
    contentDiv.appendChild(img);
  }

  if (text) {
    contentDiv.innerHTML = processMessageText(text);

    contentDiv.querySelectorAll('.doctor-block').forEach(block => {
      block.addEventListener('click', () => {
        const details = block.querySelector('.doctor-details');
        if (details) {
          details.classList.toggle('active');
        }
      });
    });
  }

  messageDiv.appendChild(contentDiv);

  const timeSpan = document.createElement('span');
  timeSpan.classList.add('message-time');
  timeSpan.textContent = formatTime(new Date());
  messageDiv.appendChild(timeSpan);

  messagesEl.appendChild(messageDiv);
  scrollToBottom();
}

function processMessageText(text) {
  // Обработка тегов <doctor>
//  text = text.replace(/<doctor>(.*?)<\/doctor>/g, (match, content) => {
//    const doctorInfo = content.split('–')[0].trim();
//    const description = content.split('–').length > 1 ? content.split('–')[1].trim() : '';
//
//    const doctorName = doctorInfo.split('(')[0].trim();
//    const specialty = doctorInfo.includes('(')
//      ? doctorInfo.match(/\((.*?)\)/)[1]
//      : 'Специалист';
//
//    return `
//      <div class="doctor-block">
//        <div class="doctor-name">${"Имя не известно"}</div>
//        <div class="doctor-specialty">${specialty}</div>
//        <div class="doctor-details">
//          <div class="doctor-description">${description || 'Этот специалист поможет диагностировать и лечить соответствующие заболевания.'}</div>
//        </div>
//      </div>
//    `;
//  });

  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
  text = text.replace(/\n\n/g, '<br><br>');
  text = text.replace(/\n/g, '<br>');

  text = text.replace(/(\d+\.\s+.*?(<br>|$))/g, '<li>$1</li>');
  text = text.replace(/<li>(.*?)<br><\/li>/g, '<li>$1</li>');
  text = text.replace(/(<li>.*?<\/li>)+/g, '<ol>$&</ol>');

  return text;
}

// Функция для отображения индикатора набора сообщения
function showTypingIndicator() {
  const typingDiv = document.createElement('div');
  typingDiv.classList.add('typing-indicator');
  typingDiv.id = 'typing';

  typingDiv.innerHTML = `
    <span></span>
    <span></span>
    <span></span>
  `;

  messagesEl.appendChild(typingDiv);
  scrollToBottom();
}

// Функция для скрытия индикатора набора
function hideTypingIndicator() {
  const typing = document.getElementById('typing');
  if (typing) typing.remove();
}

// Функция для прокрутки вниз
function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Функция для форматирования времени
function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Обработчик отправки сообщения
async function sendMessage() {
  const text = userInput.value.trim();
  const file = fileInput.files[0];

  if (!text && !file) return;

  // Создаем FormData для отправки
  const formData = new FormData();
  if (text) formData.append('message', text);
  if (file) formData.append('file', file);

  // Добавляем сообщение пользователя
  if (file) {
    const imageUrl = URL.createObjectURL(file);
    addMessage(text, 'user', { imageUrl });
  } else {
    addMessage(text, 'user');
  }

  // Очищаем поля ввода
  userInput.value = '';
  fileInput.value = '';
  adjustTextareaHeight();

  // Показываем индикатор набора
  showTypingIndicator();

  try {
    let response;

    if (file) {
      response = await fetch(`${API_BASE_URL}/upload-image`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      // Показываем маршрутизацию, если есть
      if (data.routing) {
        addMessage(data.routing, 'bot', { isRouting: true });
        await new Promise(resolve => setTimeout(resolve, 1500));
      }

      // Показываем ответ
      if (data.response) {
        addMessage(data.response, 'bot');
      }

    } else {
      response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `message=${encodeURIComponent(text)}`
      });

      const data = await response.json();

      // Показываем маршрутизацию, если есть
      if (data.routing) {
        addMessage(data.routing, 'bot', { isRouting: true });
        await new Promise(resolve => setTimeout(resolve, 1500));
      }

      // Показываем ответ
      if (data.response) {
        addMessage(data.response, 'bot');
      }
    }

  } catch (error) {
    console.error('Ошибка:', error);
    addMessage('Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.', 'bot');
  } finally {
    // Убираем индикатор набора
    hideTypingIndicator();
  }
}

// Функция для автоматического увеличения высоты textarea
function adjustTextareaHeight() {
  userInput.style.height = 'auto';
  userInput.style.height = `${Math.min(userInput.scrollHeight, 120)}px`;
}

// Обработчики событий
sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

userInput.addEventListener('input', adjustTextareaHeight);

// Инициализация - приветственное сообщение
setTimeout(() => {
  addMessage('Здравствуйте! Я AI-терапевт. Опишите ваши симптомы или загрузите фото проблемного участка, и я постараюсь помочь.', 'bot');
}, 500);