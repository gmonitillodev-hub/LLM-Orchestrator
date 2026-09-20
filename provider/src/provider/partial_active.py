import asyncio
import os
from random import randrange, choice
import time
import uvicorn
from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse
from dto import InferenceRequest
from constants import random_responses
from decorators.response_formatter import response_formatter
from decorators.execution_handler import calculate_exe_time

partial = FastAPI()


@partial.get("/health")
async def health():
    return {"status": "available"}


@partial.get('/system_info')
async def system_info():
    return {
        "version": "1.0.0",
        "author": "Giuseppe Monitillo",
        "description": "LLM Mock provider - This provider will return always 200 and proper responses",
        "status": "PartiallyAvailable"
    }


@partial.post('/api/v1/inference')
@response_formatter
@calculate_exe_time
async def inference(
        payload: InferenceRequest,
):
    """ Partial active -> 30% of 429 error """
    return_too_many_requests = ((randrange(1, 100)) < 31)
    if return_too_many_requests:
        raise HTTPException(status_code=429)

    """ Process execution simulation """
    await asyncio.sleep(randrange(5, 10))

    return JSONResponse(content=(choice(random_responses.LLM_MOCK_RESPONSES)), status_code=200)


if __name__ == "__main__":
    host = os.getenv("PROVIDER_HOST", "127.0.0.1")
    port = int(os.getenv("PROVIDER_PORT", "8100"))

    uvicorn.run(
        "provider.main:partial",
        host=host,
        port=port,
        reload=True,
    )
