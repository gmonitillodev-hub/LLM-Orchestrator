import asyncio
from typing import Optional

import requests
from pydantic import BaseModel

from classes.logger import setup_client_logger


class LlmResponse(BaseModel):
    is_failed: bool
    response: Optional[dict] = None
    status_code: int
    operation: str


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class LlmClient(metaclass=SingletonMeta):

    def __init__(self, client, config):
        self.host_name = config.get(f"LLM Client {client}", "host_name")

        self.logger = setup_client_logger(False)

    async def call_llm(self, content, operation, retry=0) -> LlmResponse:
        response = await asyncio.to_thread(
            requests.post,
            f"{self.host_name}/api/v1/inference",
            json={"message": content},
        )

        if response.status_code == 200:
            return LlmResponse(**{
                "is_failed": False,
                "status_code": response.status_code,
                "response": response.json(),
                "operation": operation
            })

        else:

            if retry < 2:

                self.logger.debug(f"Retrying {operation} - {retry+1}")

                await asyncio.sleep(0.3)
                return await self.call_llm(content, operation, retry + 1)

            else:

                self.logger.error(f"Error {response.status_code} - {operation}")

                return LlmResponse(**{
                    "is_failed": True,
                    "status_code": response.status_code,
                    "response": response.json(),
                    "operation": operation,
                })
