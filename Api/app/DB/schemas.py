from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str | None = None
    user_message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
