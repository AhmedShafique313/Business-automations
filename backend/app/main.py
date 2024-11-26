from fastapi import FastAPI
from app.routers import ai

app = FastAPI()

# Include the AI router
app.include_router(ai.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Business Platform API!"}
