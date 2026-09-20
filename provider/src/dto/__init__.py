from pydantic import BaseModel

from .inference_dto import InferenceRequest

__all__ = ["InferenceRequest"]

class ProviderResponse(BaseModel):
    data: str
    timestamp: float