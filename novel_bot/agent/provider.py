import os
from openai import AsyncOpenAI
from novel_bot.config.settings import settings
from loguru import logger
from typing import Any, AsyncGenerator

class LLMProvider:
    def __init__(self):
        api_key = settings.NVIDIA_API_KEY
        base_url = settings.NVIDIA_BASE_URL

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = settings.model_name
        logger.info(f"Initialized LLM Provider with model: {self.model} at {base_url}")

    async def chat(self, messages: list[dict], tools: list[dict] = None) -> Any:
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.9,
            }
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message
        except Exception as e:
            logger.error(f"LLM API Error: {e}")
            raise

    async def stream_chat(
        self, 
        messages: list[dict], 
        tools: list[dict] = None,
        stream_callback=None
    ) -> AsyncGenerator[str, None]:
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.9,
                "stream": True,
            }
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            response = await self.client.chat.completions.create(**params)
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    if stream_callback:
                        stream_callback(content)
                    yield content
            
        except Exception as e:
            logger.error(f"LLM Stream Error: {e}")
            raise

from typing import Any
