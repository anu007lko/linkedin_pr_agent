import os
from dotenv import load_dotenv

load_dotenv()

def _sanitize(val: str) -> str:
    if val:
        # Replace non-breaking spaces and strip outer whitespaces
        return val.replace('\xa0', ' ').strip()
    return val

GEMINI_API_KEY = _sanitize(os.getenv("GEMINI_API_KEY"))
GROQ_API_KEY = _sanitize(os.getenv("GROQ_API_KEY"))
UNSPLASH_ACCESS_KEY = _sanitize(os.getenv("UNSPLASH_ACCESS_KEY"))
ANTHROPIC_API_KEY = _sanitize(os.getenv("ANTHROPIC_API_KEY"))
HUNTER_API_KEY = _sanitize(os.getenv("HUNTER_API_KEY"))
PROSPEO_API_KEY = _sanitize(os.getenv("PROSPEO_API_KEY"))
SNOV_CLIENT_ID = _sanitize(os.getenv("SNOV_CLIENT_ID"))
SNOV_CLIENT_SECRET = _sanitize(os.getenv("SNOV_CLIENT_SECRET"))
LINKEDIN_ACCESS_TOKEN = _sanitize(os.getenv("LINKEDIN_ACCESS_TOKEN"))
GMAIL_ADDRESS = _sanitize(os.getenv("GMAIL_ADDRESS"))
GMAIL_APP_PASSWORD = _sanitize(os.getenv("GMAIL_APP_PASSWORD"))
NOTIFICATION_EMAIL = _sanitize(os.getenv("NOTIFICATION_EMAIL"))
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"

