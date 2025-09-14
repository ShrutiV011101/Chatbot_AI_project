import uuid
from fastapi import APIRouter
from app.DB import schemas
from app.Service.chatService import chat_with_bot_service

chatRouter = APIRouter()

@chatRouter.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_bot(request: schemas.ChatRequest):
    print("inside /chat endpoint ", request)    
    return chat_with_bot_service(request)