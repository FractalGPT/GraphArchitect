import requests
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class FractalGPTApi:
    """
    Клиент для взаимодействия с API FractalGPT.
    """

    def __init__(self, api_key: str, base_url: str = "https://fractalgpt.ru/api/qa") -> None:
        """
        Инициализация клиента FractalGPTApi.

        Args:
            api_key (str): API ключ для доступа к FractalGPT.
            base_url (str, optional): Базовый URL API. По умолчанию "https://fractalgpt.ru/api/qa".
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def upload_file(
        self,
        index_name: str,
        document_type: str,
        document_name: str,
        file_path: str,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Загружает файл в FractalGPT.

        Args:
            index_name (str): Имя индекса.
            document_type (str): Тип документа.
            document_name (str): Название документа.
            file_path (str): Путь к файлу для загрузки.
            timeout (int, optional): Таймаут запроса в секундах. По умолчанию 10.

        Returns:
            Dict[str, Any]: Ответ API с полями "success" и "error_message".
        """
        url = f"{self.base_url}/upload"
        try:
            with open(file_path, "rb") as file:
                data = list(file.read())
            payload = {
                "index_name": index_name,
                "document_type": document_type,
                "document_name": document_name,
                "data": data
            }
            response = requests.post(url, headers=self.headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Ошибка загрузки файла: %s", e)
            return {"success": False, "error_message": str(e)}

    def get_answer(
        self,
        index_name: str,
        question: str,
        lang: str,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Получает ответ от FractalGPT по заданному вопросу.

        Args:
            index_name (str): Имя индекса.
            question (str): Вопрос пользователя.
            lang (str): Язык для ответа.
            timeout (int, optional): Таймаут запроса. По умолчанию 10.

        Returns:
            Dict[str, Any]: Ответ API с полями "success", "answer" и "error_message".
        """
        url = f"{self.base_url}/get-answer"
        payload = {
            "index_name": index_name,
            "question": question,
            "lang": lang
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Ошибка получения ответа: %s", e)
            return {"success": False, "answer": "", "error_message": str(e)}

    def delete_index(
        self,
        index_name: str,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Удаляет индекс из FractalGPT.

        Args:
            index_name (str): Имя индекса для удаления.
            timeout (int, optional): Таймаут запроса. По умолчанию 10.

        Returns:
            Dict[str, Any]: Ответ API с полями "success" и "error_message".
        """
        url = f"{self.base_url}/delete?index_name={index_name}"
        try:
            response = requests.delete(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Ошибка удаления индекса: %s", e)
            return {"success": False, "error_message": str(e)}
