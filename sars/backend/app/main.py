from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .models import Base
from .routes import auth, student, teacher

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SARS", description="Student Academic Risk System", version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
    ],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(student.router)
app.include_router(teacher.router)

@app.get("/")
def root():
    return {"message": "SARS API running", "docs": "/docs"}


