import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = [
    "JIRA_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "GROQ_API_KEY",
]


def load_config() -> dict:
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        raise SystemExit(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Copy .env.example to .env and fill in the values."
        )

    return {
        "jira_url": os.environ["JIRA_URL"].rstrip("/"),
        "jira_email": os.environ["JIRA_EMAIL"],
        "jira_api_token": os.environ["JIRA_API_TOKEN"],
        "jira_project": os.getenv("JIRA_PROJECT", ""),
        "groq_api_key": os.environ["GROQ_API_KEY"],
        "groq_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    }
