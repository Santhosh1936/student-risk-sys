import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Absolute path to the DB file — always next to this config.py regardless of cwd
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_DB_URL = f"sqlite:///{os.path.join(_BACKEND_DIR, 'sars.db')}"

# Force .env file to override any stale environment variables
load_dotenv(os.path.join(_BACKEND_DIR, ".env"), override=True)

class Settings(BaseSettings):
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_USE_RANDOM_32_CHARS"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = _DEFAULT_DB_URL
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = os.path.join(_BACKEND_DIR, ".env")

settings = Settings()
