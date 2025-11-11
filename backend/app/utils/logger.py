import json
import os
from datetime import datetime

LOG_FILE = "logs.json"

def log_interaction(user_id: str, instruction: str, user_text: str, ai_response: str, usage: dict):
    """Logs every GPT interaction safely to a JSON file."""

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "instruction": instruction,
        "user_text": user_text,
        "ai_response": ai_response,
        "token_usage": usage,
    }

    # Ensure file exists
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)

    # ✅ Safely load or reset if file is empty/corrupted
    try:
        with open(LOG_FILE, "r") as f:
            content = f.read().strip()
            data = json.loads(content) if content else []
    except json.JSONDecodeError:
        data = []  # file corrupted, start fresh

    # Add the new log entry
    data.append(log_entry)

    # ✅ Write back safely
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)
