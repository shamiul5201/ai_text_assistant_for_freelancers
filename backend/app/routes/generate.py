import os
from fastapi import APIRouter, HTTPException, Depends
from app.models.promp_model import GenerateRequest, GenerateResponse
from app.utils.logger import log_interaction
from openai import OpenAI
from dotenv import load_dotenv

from app.core.auth import verify_token


load_dotenv()
router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/generate", response_model=GenerateResponse)
async def generate_text(payload: GenerateRequest, username: str = Depends(verify_token)):
    """Protected AI generation endpoint
    Requires valid JWT token"""

    try:
        prompt = f"{payload.instruction}\n\nText:\n{payload.user_text}"
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens= 300
        )

        result = completion.choices[0].message.content.strip()
        usage = completion.usage.dict() if hasattr(completion, "usage") else {}

        # Log the entire interaction
        log_interaction(
            user_id = username,
            instruction = payload.instruction,
            user_text = payload.user_text,
            ai_response = result,
            usage = usage 
        )

        return GenerateResponse(result=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
