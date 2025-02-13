import requests

url = 'http://localhost:5126/api/serve'
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}
data = {
    "question": "Кто такой кот?"
}

response = requests.post(url, headers=headers, json=data)

# Выводим статус код и ответ
print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.text}")