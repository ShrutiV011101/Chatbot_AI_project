from typing import Dict, List
import uuid
from fastapi import HTTPException
from app.DB import schemas
from app.extractEnvVariables import api_key
from openai import OpenAI

print(f"API Key: {api_key}")  # Debug print to check if the API key is loaded correctly
aiClient = OpenAI(api_key= api_key)

chat_sessions: Dict[str, List[Dict[str, str]]] = {}

def chat_with_bot_service(request: schemas.ChatRequest):
    # If no session_id provided, create one
    session_id = request.session_id or str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    # Initialize history if new session
    if session_id not in chat_sessions:
        print("inside new session")
        chat_sessions[session_id] = []

    # Append user message
    chat_sessions[session_id].append({"role": "user", "content": request.user_message})

    print(f"Chat History: {chat_sessions[session_id]}")
    # Call OpenAI with full history
    try:
        response = aiClient.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_sessions[session_id],
            temperature=0.7
        )
        print(f"OpenAI Response: {response}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    bot_reply = response.choices[0].message.content
    print(f"Bot Reply: {bot_reply}")
    # Append bot reply to history
    chat_sessions[session_id].append({"role": "assistant", "content": bot_reply})

    return schemas.ChatResponse(session_id=session_id, reply=bot_reply)