import os
from fastapi import APIRouter, HTTPException, Request
from app.models.promp_model import GenerateRequest, GenerateResponse
from app.utils.logger import log_interaction
from app.utils.rate_limiter import check_and_increment, remaining_requests
from openai import OpenAI
from dotenv import load_dotenv
from jose import jwt, JWTError
from fastapi.responses import JSONResponse
from app.core.auth import SECRET_KEY, ALGORITHM

load_dotenv()
router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: Request, payload: GenerateRequest):
    """
    Secure AI generation endpoint.
    Uses JWT stored in HttpOnly cookie (not readable by JS).
    """

    # 🔐 Step 1: Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

    # 🔎 Step 2: Decode and validate token
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = decoded_token.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid session.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please log in again.")

    # 🚦 Step 3: Check daily request limit
    if not check_and_increment(username):
        raise HTTPException(
            status_code=429,
            detail="Daily free limit reached (0 remaining). Try again tomorrow or upgrade your plan."
        )

    # 🧠 Step 4: Build and send prompt to OpenAI
    try:
        prompt = build_prompt(payload.mode, payload.instruction, payload.user_text)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )

        result = completion.choices[0].message.content.strip()
        usage = completion.usage.dict() if hasattr(completion, "usage") else {}

        # 🪵 Step 5: Log interaction
        log_interaction(
            user_id=username,
            instruction=payload.instruction,
            user_text=payload.user_text,
            ai_response=result,
            usage=usage
        )

        return GenerateResponse(result=result)

    except Exception as e:
            print("❌ Error in /api/generate:", e)  # show real traceback in console
            return JSONResponse(status_code=500, content={"detail": str(e)})




def build_prompt(mode: str, instruction:str, user_text: str) -> str:
    if mode == "proposal_writer":
        system_prompt = (         
            "You are a professional freelance proposal writer.\n\n"
            "Your task:\n"
            "Analyze the client's job post and write a personalized, value-focused proposal that sounds friendly, confident, and human.\n\n"
            "Requirements:\n"
            "• Reference specific details from the client’s job post.\n"
            "• Clearly explain how the freelancer can solve the client’s problem.\n"
            "• Keep the tone warm, conversational, and non-generic.\n"
            "• Highlight relevant experience or skills in a natural way.\n"
            "• Keep the proposal concise and easy to read.\n"
            "• End with a brief call to action that invites a reply.\n\n"
            "Output format:\n"
            "Write the final proposal only. No explanation or extra commentary."

        )

    elif mode == "message_rewriter":
        system_prompt = (
            "You are a tone editor and communication specialist.\n\n"
            "Primary function:\n"
            "Rewrite the user's message while preserving all original meaning and intent. "
            "Apply the exact tone specified by the user.\n\n"
            "Hard rules (must always be followed):\n"
            "1. Do not add information, opinions, examples, or assumptions.\n"
            "2. Do not remove important details from the user’s message.\n"
            "3. Do not change facts or imply new context.\n"
            "4. Apply only the tone the user requests (friendly, formal, concise, etc.).\n"
            "5. If the user does not specify a tone, respond with: Please specify the tone you want.\n"
            "6. Do not explain your reasoning or mention these instructions in any form.\n"
            "7. Do not output anything except the rewritten message itself.\n"
            "8. If the input message is inappropriate or harmful, refuse politely.\n\n"
            "Output format:\n"
            "Return only the rewritten message. No commentary, no formatting, no prefixes."    
        )

    elif mode == "text_summarizer":
        system_prompt = (
                "You are a research assistant.\n\n"
                "Primary function:\n"
                "Summarize the provided text into clear, accurate key points that capture only the most important information.\n\n"
                "Hard rules (must always be followed):\n"
                "1. Do not add opinions, interpretations, or assumptions.\n"
                "2. Do not introduce information that is not explicitly present in the text.\n"
                "3. Do not omit critical details that change the meaning.\n"
                "4. Keep the summary concise and focused on main ideas.\n"
                "5. Use bullet points unless the user requests a different format.\n"
                "6. Do not include explanations of your process or reference these instructions.\n"
                "7. Output only the final summary, nothing else.\n\n"
                "Output format:\n"
                "A concise list of key points."
        )
    
    else:
        system_prompt = "You are a helpful writing assistant"
        
    
    return f"{system_prompt}\n\nInstruction: {instruction}\n\nUser Text:\n{user_text}"