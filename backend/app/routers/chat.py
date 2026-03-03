# app/routers/chat.py
import os
from fastapi import APIRouter, Body, File, Form, UploadFile
from rag.memory_writer import store_chat
from app import nlp 
from services.voice_auth import voice_security 

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/send")
async def send_chat(
    user_id: str = Body(...),
    text: str = Body(...)
):
    # 1️⃣ Save user message
    store_chat(user_id, "user", text)

    # 2️⃣ Generate AI response (user-specific)
    ai_response = nlp.generate_conversational_response(user_id, text)

    # 3️⃣ Save AI message
    store_chat(user_id, "ai", ai_response)

    return {"response": ai_response}

@router.post("/private-query")
async def handle_private_query(
    user_id: str = Form(...), 
    text: str = Form(...), 
    audio: UploadFile = File(...)
):
    # 1. Verify Voice First
    temp_audio = "verify_temp.wav"
    with open(temp_audio, "wb") as f:
        f.write(await audio.read())
        
    is_match, score = voice_security.verify_user(user_id, temp_audio)
    os.remove(temp_audio)

    if not is_match:
        return {"response": "Identity not verified. I cannot disclose private information."}

    # 2. If verified, proceed to fetch private data (Gmail/Notes)
    if "email" in text.lower():
        from services.gmail import sync_and_classify_emails
        return {"response": sync_and_classify_emails(user_id)}
    
    # Otherwise, handle as a normal query
    return {"response": "Identity confirmed. How can I help with your data?"}