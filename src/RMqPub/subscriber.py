# Простой пример создания очереди, который будет имитировать задачи после ЕЯИ.

# Для проверки работы основного приложения необходимо установить зависимости pika.

import pika
import json
import random
import time
import threading

# TODO Сделать класс типа конструктор, для того чтобы собирать любые тестовые объекты, похожие на
# реальные пользовательские запросы.

# Список допустимых параметров для поля "F_D" и "d"
allowed_types = ["wav", "mp3", "mp4", "raw"]


# TODO генерировать переменное количество сигнатур, и разные сигнатуры.
def generate_signatures():
    pass


def generate_data():
    data = {
        "MASL": {
            "X": [
                {
                    "s": {
                        "F_D": random.choice(allowed_types),
                        "F_S": "raw",
                    },
                    "d": "1.wav",
                }
            ],
            "I": {
                "s": {"F_D": "complex_vector", "F_S": "specter"},
                "F_I": {"type": "chart", "modify": ["abs", "half"]},
            },
        },
        "Domain": "Bio",
        "MaxAnswerTime": 30,
        "probTrue": 0.8,
        "costApi": 10,
        "minAgentReward": 0.2,
    }
    return data


# Отправляет данные по Rabbit.
def publish_to_rabbitmq(client_id, delay):
    params = pika.ConnectionParameters(
        host="45.88.90.36",
        port=5672,
        credentials=pika.PlainCredentials("paw", "T2EdYb=iN^"),
    )

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange="client_exchange", exchange_type="direct")
    channel.queue_declare(queue="client_queue", durable=True)
    channel.queue_bind(
        exchange="client_exchange",
        queue="client_queue",
        routing_key="client_routing_key",
    )
    while True:
        message = generate_data()
        message_json = json.dumps(message)
        channel.basic_publish(
            exchange="client_exchange",
            routing_key="client_routing_key",
            body=message_json,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Чтобы не потерять
            ),
        )
        print(f"Sent: {message_json}")
        time.sleep(delay)


def test_on_load():
    num_clients = 1
    delay = 1
    threads = []
    for i in range(num_clients):
        # Запуск каждого клиента в отдельном потоке
        thread = threading.Thread(target=publish_to_rabbitmq, args=(i + 1, delay))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


# Основной цикл для генерации и отправки данных
if __name__ == "__main__":
    # ВКЛЮЧИТЬ, ЕСЛИ НЕОБХОДИМО ЧТОБЫ ПИСАЛ ОДИН ПОТОК
    # publish_to_rabbitmq(1, 10)
    test_on_load()
