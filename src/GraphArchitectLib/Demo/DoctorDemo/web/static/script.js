// Получаем ссылки на элементы
const messagesEl = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

// Функция добавления сообщения в чат
function addMessage(text, sender = 'user') {
  const msgDiv = document.createElement('div');
  msgDiv.classList.add('message', sender);
  msgDiv.textContent = text;
  messagesEl.appendChild(msgDiv);
  // Прокручиваем область сообщений вниз
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Обработчик нажатия кнопки "Отправить"
sendBtn.addEventListener('click', async () => {
  const text = userInput.value.trim();
  if (!text) return;

  // Добавляем сообщение пользователя
  addMessage(text, 'user');
  userInput.value = '';

  // Отправляем POST-запрос на /chat
  const formData = new FormData();
  formData.append('message', text);

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    // Добавляем ответ бота
    addMessage(data.response, 'bot');
  } catch (error) {
    console.error('Ошибка:', error);
    addMessage('Ошибка сервера', 'bot');
  }
});
