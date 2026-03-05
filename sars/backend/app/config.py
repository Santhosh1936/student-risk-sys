from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_USE_RANDOM_32_CHARS"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite:///./sars.db"
    class Config:
        env_file = ".env"

settings = Settings()
