import asyncio
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ai.models import ChatRequest, ChatResponse
from ai.service import AIService

# Initialize AI service
ai_service = AIService()

# Create AI router
ai_router = APIRouter(prefix="/api", tags=["AI"])

@ai_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat with AI assistant with MCP tools"""
    response_text = await ai_service.generate_response(
        message=request.message,
        conversation_history=request.conversation_history
    )

    return ChatResponse(
        response=response_text,
        timestamp=datetime.now().isoformat()
    )

@ai_router.post("/chat/stream")
async def chat_with_ai_stream(request: ChatRequest):
    """Stream chat response from AI assistant using Server-Sent Events"""
    import json

    async def generate():
        try:
            async for chunk in ai_service.stream_response(
                message=request.message,
                conversation_history=request.conversation_history
            ):
                # Chunk is already JSON string from service
                yield f"data: {chunk}\n\n"
                # Force flush for immediate delivery
                await asyncio.sleep(0)  # Yield control to ensure data is sent

            # Send completion signal
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable proxy buffering
        }
    )