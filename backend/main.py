from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Import AI router
from ai.routes import ai_router
from auth.azure_auth import optional_auth

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="ExCom AI Chat API",
    version="1.0.0",
    description="AI Chat Service API"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:8000",
        "http://localhost:3050",
        "https://f2cd2ae2d84a.ngrok-free.app",
        "http://localhost"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include AI router
app.include_router(ai_router)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ExCom AI Chat"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "ExCom AI Chat API",
        "version": "1.0.0",
        "endpoints": [
            "/api/health",
            "/api/chat",
            "/api/chat/stream",
            "/docs"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)