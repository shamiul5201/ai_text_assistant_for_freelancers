# backend/app/utils/rate_limiter.py
import json
import os
from datetime import date

LIMIT_FILE = "usage_limits.json"
DAILY_LIMIT = 10

def load_limits():
    if not os.path.exists(LIMIT_FILE):
        with open(LIMIT_FILE, "w") as f:
            json.dump({}, f)
    with open(LIMIT_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_limits(data):
    with open(LIMIT_FILE, "w") as f:
        json.dump(data, f, indent=2)

def check_and_increment(username: str) -> bool:
    """
    Returns True if user can proceed, False if limit reached.
    Automatically resets daily.
    """
    today = str(date.today())
    data = load_limits()

    if username not in data:
        data[username] = {"date": today, "count": 0}

    # Reset daily count if date changed
    if data[username]["date"] != today:
        data[username] = {"date": today, "count": 0}

    if data[username]["count"] >= DAILY_LIMIT:
        return False

    # Increment usage
    data[username]["count"] += 1
    save_limits(data)
    return True

def remaining_requests(username: str) -> int:
    today = str(date.today())
    data = load_limits()

    if username not in data or data[username]["date"] != today:
        return DAILY_LIMIT

    return DAILY_LIMIT - data[username]["count"]
