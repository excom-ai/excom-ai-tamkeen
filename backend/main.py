from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# CORS configuration - in production, same-origin so less critical
# But keeping for local development with separate frontend
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:8000",
    "http://localhost:3050",
    "https://f2cd2ae2d84a.ngrok-free.app",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

# Root API endpoint - only served if not handled by static files
@app.get("/api")
async def api_root():
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

# Serve React app - this must be AFTER all API routes
# Only serve static files if they exist (for production)
if os.path.exists("static"):
    # Serve static files for all non-API routes
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)