import BaseModel
from pydantic import BaseModel

class InferenceRequest(BaseModel):
    message: str

