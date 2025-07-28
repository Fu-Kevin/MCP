# mcp/config/settings.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

# === OpenAI or NLP Settings ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# === Google Calendar Settings ===
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly"
]

# === Microsoft Graph (Outlook) Settings ===
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "")

# === Email Settings ===
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# === Default Timezone ===
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")

# === Debug Mode ===
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
