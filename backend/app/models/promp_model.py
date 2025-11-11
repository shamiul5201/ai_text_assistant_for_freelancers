from pydantic import BaseModel

class GenerateRequest(BaseModel):
    mode: str
    instruction: str
    user_text: str

class GenerateResponse(BaseModel):
    result: str