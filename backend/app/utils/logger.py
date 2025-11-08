import json
import os
from datetime import datetime

LOG_FILE = "logs.json"

def log_interaction(user_id: str, instruction:str, user_text: str, ai_response:str, usage:dict):
    """Logs every GPT interaction to a JSON file
        Each entry includes timestamps, token, and content
    """

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "instruction": instruction,
        "user_text": user_text,
        "ai_response": ai_response,
        "token_usage": usage
    }


    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            json.dump([], f)

    with open(LOG_FILE, "r+") as f:
        data = json.load(f)
        data.append(log_entry)
        f.seek(0)
        json.dump(data, f, indent=2)

        