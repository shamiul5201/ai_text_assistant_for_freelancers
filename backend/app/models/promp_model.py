from pydantic import BaseModel

class GenerateRequest(BaseModel):
    instruction: str
    user_text: str

class GenerateResponse(BaseModel):
    result: str