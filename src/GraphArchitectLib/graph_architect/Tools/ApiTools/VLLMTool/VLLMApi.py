import requests


class VLLMApi:
    def __init__(self, vllm_host: str, model_name: str, prompt: str) -> None:
        self.vllm_host = vllm_host
        self.model_name = model_name
        self.prompt = prompt

    def query_llm(
            self, question: str, temperature: float = 0.2, top_p: float = 0.95,
            top_k: int = 30, max_len: int = 5000
    ) -> str:
        headers = {"Content-Type": "application/json"}

        payload = {
            "repetition_penalty": 1.06,
            "top_p": top_p,
            "top_k": top_k,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_len,
            "messages": [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": question}
            ],
            "model": self.model_name
        }

        try:
            response = requests.post(self.vllm_host, headers=headers, json=payload)
            response.raise_for_status()
            ans = response.json()
            return ans.get('choices', [{}])[0].get('message', {}).get('content', "")
        except requests.exceptions.RequestException as e:
            return f"Request failed: {e}"
        except (KeyError, IndexError) as e:
            return f"Unexpected response format: {e}"