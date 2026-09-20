import asyncio
import os
from random import random

import uvicorn
from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse

from dto import InferenceRequest
import time
import random
from constants import random_responses
from decorators.response_formatter import response_formatter
from decorators.execution_handler import calculate_exe_time

full = FastAPI()


@full.get("/health")
async def health():
    return {"status": "unavailable"}


@full.get('/system_info')
async def system_info():
    return {
        "version": "1.0.0",
        "author": "Giuseppe Monitillo",
        "description": "LLM Mock provider - This provider will return always 200 and proper responses",
        "status": "PartiallyAvailable"
    }


@full.post('/api/v1/inference')
@response_formatter
@calculate_exe_time
async def inference(
        payload: InferenceRequest,
):
    ''' Full active -> 0% of 429 error '''

    ''' Process execution simulation '''
    await asyncio.sleep(random.randrange(3, 5))

    return JSONResponse(content=(f"{random.choice(random_responses.LLM_MOCK_RESPONSES)}"), status_code=200)


if __name__ == "__main__":
    host = os.getenv("PROVIDER_HOST", "127.0.0.1")
    port = int(os.getenv("PROVIDER_PORT", "8000"))

    uvicorn.run(
        "provider.main:full",
        host=host,
        port=port,
        reload=True,
    )
