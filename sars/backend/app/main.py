import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .models import Base
from .routes import auth, student, teacher
from .config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sars")

# ── Security check — abort startup if SECRET_KEY is insecure ──────────────────
_INSECURE_DEFAULTS = {
    "CHANGE_THIS_IN_PRODUCTION_USE_RANDOM_32_CHARS",
    "change_this", "secret", "secret_key", "",
}
if settings.SECRET_KEY in _INSECURE_DEFAULTS or len(settings.SECRET_KEY) < 32:
    raise RuntimeError(
        "\n\nSECURITY ERROR: SECRET_KEY is not set or is insecure.\n"
        "Run this to generate a secure key:\n"
        "  python -c \"import secrets; print(secrets.token_hex(32))\"\n"
        "Then add it to backend/.env as: SECRET_KEY=<your_key>\n"
    )

Base.metadata.create_all(bind=engine)
logger.info("SARS backend starting up... environment=%s", settings.ENVIRONMENT)

app = FastAPI(
    title="SARS",
    description="Student Academic Risk System",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(student.router)
app.include_router(teacher.router)

@app.get("/")
def root():
    return {"message": "SARS API running", "docs": "/docs"}
