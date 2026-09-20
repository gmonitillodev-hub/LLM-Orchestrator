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

inactive = FastAPI()


@inactive.get("/health")
async def health():
    return {"status": "unavailable"}


@inactive.get('/system_info')
async def system_info():
    return {
        "version": "1.0.0",
        "author": "Giuseppe Monitillo",
        "description": "LLM Mock provider - This provider will return always 200 and proper responses",
        "status": "PartiallyAvailable"
    }


@inactive.post('/api/v1/inference')
@response_formatter
@calculate_exe_time
async def inference(
        payload: InferenceRequest,
):
    ''' Partial active -> 50% of 429 error '''

    availability_score = random.randrange(1, 100)

    if (availability_score < 20):
        raise HTTPException(status_code=500)

    elif (21 < availability_score < 80):
        raise HTTPException(status_code=429)

    ''' Process execution simulation '''
    await  asyncio.sleep(random.randrange(10, 15))

    return JSONResponse(content=(random.choice(random_responses.LLM_MOCK_RESPONSES)), status_code=200)


if __name__ == "__main__":
    host = os.getenv("PROVIDER_HOST", "127.0.0.1")
    port = int(os.getenv("PROVIDER_PORT", "8200"))

    uvicorn.run(
        "provider.main:inactive",
        host=host,
        port=port,
        reload=True,
    )
