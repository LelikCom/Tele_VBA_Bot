import os
import aiohttp
from dotenv import load_dotenv
from typing import Literal, Optional

load_dotenv()


class DeepSeekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
        self.models = {
            "chat": "deepseek-chat",
            "assistant": "deepseek-chat",
            "deepthink": "deepseek-chat",
            "search": "deepseek-chat"
        }

    def _prepare_payload(
            self,
            messages: list[dict],
            mode: Literal["chat", "deepthink", "search"],
            web_search: bool
    ) -> dict:
        """Формирует тело запроса в соответствии с режимом работы"""
        system_prompt_map = {
            "chat": "You are a helpful assistant",
            "deepthink": "Think deeply and reason step by step",
            "search": "You have access to real-time web search. Use it when necessary."
        }

        return {
            "model": self.models[mode],
            "messages": [
                {"role": "system", "content": system_prompt_map[mode]},
                *messages
            ],
            "temperature": 0.7 if mode == "deepthink" else 0.3,
            "top_p": 0.95 if mode == "search" else 0.8,
            "web_search": web_search and mode in ["search", "deepthink"],
            "stream": False
        }

    async def send_message(
            self,
            messages: list[dict],
            mode: Literal["chat", "deepthink", "search"] = "chat",
            web_search: bool = False
    ) -> str:
        """Отправляет запрос в DeepSeek API с поддержкой разных режимов"""
        if not self.api_key:
            raise RuntimeError("DeepSeek API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = self._prepare_payload(messages, mode, web_search)

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180)) as session:
                async with session.post(
                        url=self.base_url,
                        json=payload,
                        headers=headers
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if not data.get("choices"):
                        raise ValueError("Invalid API response format")

                    return data["choices"][0]["message"]["content"]

        except aiohttp.ClientError as e:
            raise RuntimeError(f"Network error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"API request failed: {str(e)}")