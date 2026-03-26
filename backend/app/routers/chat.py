import os, shutil, psycopg2.extras
from fastapi import APIRouter, Body, File, Form, UploadFile, HTTPException
from services.db import get_db
from services.db_helper import save_to_appropriate_table
from services.voice_auth import voice_security 
from rag.memory_writer import store_chat

# STT and NLP Imports
from app.stt import transcribe_audio as transcribe 
from app.nlp import (
    analyze_conversation_payload, 
    generate_conversational_response, 
    classify_audio_intent
)

router = APIRouter()

# --- Configuration & State ---
ACTIVE_SESSIONS = {} # Tracks if the user is in an active conversation {user_id: bool}
WAKE_WORDS = ["mate", "buddy", "mindmate"]
STOP_WORDS = ["stop", "no need help", "end conversation", "bye", "terminate"]
RETRIEVAL_KEYWORDS = ["what was", "what is", "history", "schedule", "plan", "show me", "did i", "future"]

# --- ROUTES ---

@router.get("/history")
async def get_chat_history(user_id: str):
    """Fetches chat history for the Memory page."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("""
            SELECT sender, text as content, created_at as time 
            FROM chat_messages WHERE user_id = %s 
            ORDER BY created_at ASC
        """, (user_id,))
        return {"history": cur.fetchall()}
    finally:
        cur.close()
        conn.close()

@router.post("/upload-audio")
async def upload_audio(user_id: str = Form(...), file: UploadFile = File(...)):
    """
    Final Agentic Router Logic:
    1. Real-time Voice Authentication (Biometric Gate).
    2. Transcription & Background Extraction (Always-On Storage).
    3. Wake-Word Detection (Session Activation).
    4. Privacy-Protected Retrieval (Blocks strangers from reading DB).
    """
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{user_id}_{file.filename}")

    try:
        # Save the incoming audio chunk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 🟢 STAGE 1: REAL-TIME VOICE AUTH (Identity Flag)
        # This is the "Security Handshake". Flag 1 = User, 0 = Other.
        is_user, score = voice_security.verify_user(user_id, file_path)
        auth_flag = 1 if is_user else 0
        username = user_id.split('@')[0] # For the "Who are you?" message

        # 🟢 STAGE 2: TRANSCRIBE
        transcript = transcribe(file_path)
        if not transcript or len(transcript.strip()) < 3:
            return {"transcript": "", "auth_flag": auth_flag, "ai_response": ""}
        
        lower_t = transcript.lower().strip()

        # 🟢 STAGE 3: SESSION MANAGEMENT (Wake/Stop)
        # Check if the user starts a command with "Mate" or "Buddy"
        if any(lower_t.startswith(word) for word in WAKE_WORDS):
            ACTIVE_SESSIONS[user_id] = True
        
        # Check if the user wants to end the interaction
        if any(word in lower_t for word in STOP_WORDS):
            ACTIVE_SESSIONS[user_id] = False
            return {
                "transcript": transcript, 
                "ai_response": "Understood. Conversation ended. I'm still monitoring for you.", 
                "auth_flag": auth_flag
            }

        # 🟢 STAGE 4: INTENT & PASSIVE MONITORING
        # Analyze the chunk for emotions, officiality, and content
        analysis = classify_audio_intent(transcript)
        # Background Extraction: Always save context silently to DB (RAG)
        extraction_msg = save_to_appropriate_table(user_id, analysis, transcript)

        # 🟢 STAGE 5: SECURITY GATE & RETRIEVAL (Privacy Logic)
        ai_response = ""
        if ACTIVE_SESSIONS.get(user_id, False):
            # Check if user is asking to READ, DELETE, or SEARCH private records
            is_retrieval_request = (
                analysis.get("decision") == "CRUD" or 
                any(k in lower_t for k in RETRIEVAL_KEYWORDS)
            )

            if is_retrieval_request:
                if auth_flag == 1:
                    # ✅ VERIFIED USER: Allow access to DB history/schedules
                    ai_response = handle_db_operation(user_id, analysis, transcript)
                else:
                    # ❌ UNVERIFIED VOICE: Security Block
                    ai_response = f"Who are you? You are not {username}. I cannot retrieve private data or change settings for an unverified voice."
            else:
                # Regular Assistant Chat (Answering doubts, general talk via RAG)
                ai_response = generate_conversational_response(user_id, transcript)

            # Log the conversation into history for the 'Memory' page
            store_chat(user_id, "user", transcript)
            store_chat(user_id, "ai", ai_response)

        return {
            "transcript": transcript,
            "ai_response": ai_response,
            "auth_flag": auth_flag,
            "extraction_log": extraction_msg,
            "session_active": ACTIVE_SESSIONS.get(user_id, False)
        }

    except Exception as e:
        print(f"❌ Critical Router Error: {e}")
        return {"error": str(e)}
    finally:
        # Clean up temporary audio files
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/send")
async def send_chat(user_id: str = Body(...), text: str = Body(...)):
    """Handles text chat from the UI."""
    try:
        # 1. Store User Msg
        store_chat(user_id, "user", text)

        # 2. Extract potential data (Notes/Tasks)
        extraction_msg = None
        try:
            analysis = analyze_conversation_payload(user_id, text)
            if analysis and analysis.get("has_data"):
                extraction_msg = save_to_appropriate_table(user_id, analysis, text, "Text Chat")
        except Exception as e:
            print(f"⚠️ Extraction failed: {e}")

        # 3. Generate AI Response via RAG
        ai_response = generate_conversational_response(user_id, text)
        if not ai_response:
            ai_response = "I'm listening, but I couldn't process a response. Try again?"

        if extraction_msg:
            ai_response += f"\n\n(Note: {extraction_msg})"
        
        # 4. Store AI Response
        store_chat(user_id, "ai", ai_response)
        
        return {"response": ai_response}

    except Exception as e:
        return {"response": "System error. Please try again.", "error": str(e)}

@router.post("/private-query")
async def handle_private_query(
    user_id: str = Form(...), 
    text: str = Form(...), 
    audio: UploadFile = File(...)
):
    """Voice-verified Gmail sync or private data access."""
    temp_audio = f"verify_{user_id}.wav"
    with open(temp_audio, "wb") as f:
        f.write(await audio.read())
        
    is_match, _ = voice_security.verify_user(user_id, temp_audio)
    os.remove(temp_audio)

    if not is_match:
        raise HTTPException(status_code=403, detail="Identity not verified.")

    if "email" in text.lower():
        from services.gmail import deep_sync_gmail
        deep_sync_gmail(user_id)
        return {"response": "Identity confirmed. I have synced your latest emails."}
    
    return {"response": "Identity confirmed. Access granted."}

def handle_db_operation(user_id: str, analysis: dict, text: str):
    """
    Executes SQL commands based on Natural Language intent.
    Only called if auth_flag == 1.
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    action = analysis.get("action", "NONE")
    category = analysis.get("category", "note")

    try:
        # --- DELETE LOGIC ---
        if action == "DELETE":
            table = "reminders" if category == "reminder" else "notes"
            cur.execute(f"DELETE FROM {table} WHERE user_id = %s AND id = (SELECT max(id) FROM {table} WHERE user_id = %s)", (user_id, user_id))
            conn.commit()
            return f"🗑️ Done. I've removed the latest {category} from your records."

        # --- RETRIEVAL / READ LOGIC ---
        elif action == "READ":
            if category == "reminder" or "schedule" in text.lower():
                cur.execute("SELECT message FROM reminders WHERE user_id = %s AND priority = 1 AND status = 'active' LIMIT 3", (user_id,))
                rows = cur.fetchall()
                tasks = ", ".join([r['message'] for r in rows])
                return f"📅 Verified. Your high-priority reminders are: {tasks}" if tasks else "You have no urgent reminders currently."
            
            # Use RAG for general reading of memories
            return generate_conversational_response(user_id, text)
            
        return "I've understood the command, but I'm not sure which record to modify. Could you be more specific?"
    
    except Exception as e:
        return f"Database error: {str(e)}"
    finally:
        cur.close()
        conn.close()