from fastapi import FastAPI

from app.api.user import router as user_router
from app.api.auth import router as auth_router


app = FastAPI(
    title="Digital Twin AI",
    version="1.0.0",
    description="Backend API for the Digital Twin AI project"
)

app.include_router(user_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "Digital Twin AI Backend Running"}


@app.get("/health")
def health():
    return {"status": "healthy"}    