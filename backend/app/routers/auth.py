from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
import os
import sys
from pydantic import BaseModel
from services.db import get_db
from services.voice_auth import voice_security
from services.gmail import deep_sync_gmail
from passlib.context import CryptContext
from pydub import AudioSegment

router = APIRouter(tags=["Authentication"])
# --- Security Helpers ---
# Standardize on passlib to avoid padding/version mismatch errors
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🟢 FORCE PRINT ON STARTUP: Copy this value from your terminal to update pgAdmin
generated_hash = pwd_context.hash("password123")
sys.stdout.write(f"\n🚀 DATABASE UPDATE REQUIRED 🚀\n")
sys.stdout.write(f"COPY THIS HASH FOR admin123: {generated_hash}\n")
sys.stdout.write(f"-------------------------------------------\n\n")
sys.stdout.flush()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, generated_hash: str):
    try:
        return pwd_context.verify(plain_password, generated_hash)
    except Exception as e:
        print(f"❌ Hash verification error: {e}")
        return False

def normalize_audio(input_path):
    """Converts audio to 16kHz Mono WAV for SpeechBrain"""
    if not os.path.exists(input_path):
        return False
    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(input_path, format="wav")
        return True
    except Exception as e:
        print(f"Normalization Error: {e}")
        return False

# --- Models ---
class UserAuth(BaseModel):
    user_id: str
    password: str

# --- Endpoints ---

@router.post("/signup")
async def signup(
    username: str = Form(...),
    user_id: str = Form(...),
    password: str = Form(...),
    voice_file: UploadFile = File(...)
):
    conn = get_db()
    cur = conn.cursor()
    
    base_dir = os.getcwd() 
    signature_dir = os.path.join(base_dir, "voice_signatures")
    os.makedirs(signature_dir, exist_ok=True)
    
    # Use standard user_id for filename to match verification logic
    file_path = os.path.join(signature_dir, f"{user_id}.wav")

    try:
        cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="User already exists")

        content = await voice_file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        await voice_file.seek(0) 

        if not normalize_audio(file_path):
            raise HTTPException(status_code=400, detail="Audio normalization failed.")

        voice_security.enroll_user(user_id, file_path)

        hashed_pw = hash_password(password)
        cur.execute(
            "INSERT INTO users (user_id, username, password_hash) VALUES (%s, %s, %s)",
            (user_id, username, hashed_pw)
        )
        conn.commit()
        return {"status": "success", "message": "Account & Voice Profile Created"}

    except Exception as e:
        if conn: conn.rollback()
        print(f"🔥 SIGNUP CRASH: {str(e)}")
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@router.post("/login")
async def login(user: UserAuth, background_tasks: BackgroundTasks):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id, password_hash FROM users WHERE user_id = %s", (user.user_id,))
        row = cur.fetchone()

        if not row or not verify_password(user.password, row[1]):
            print(f"❌ Login failed for: {user.user_id}") 
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Sync Gmail data in background upon successful login
        background_tasks.add_task(deep_sync_gmail, user.user_id, 20)
        
        return {"status": "success", "user_id": row[0]}
    finally:
        cur.close()
        conn.close()

@router.post("/enroll-voice")
async def enroll_voice(file: UploadFile = File(...), user_id: str = Form(...)):
    temp_filename = f"temp_enroll_{user_id.replace('@','_')}.wav"
    try:
        content = await file.read()
        with open(temp_filename, "wb") as buffer:
            buffer.write(content)
        
        if normalize_audio(temp_filename):
            voice_security.enroll_user(user_id, temp_filename)
            return {"status": "success", "message": "Voice Signature Saved."}
        else:
            raise HTTPException(status_code=400, detail="Invalid Audio Format")
    finally:
        if os.path.exists(temp_filename): os.remove(temp_filename)

@router.post("/login-voice")
async def login_with_voice(
    file: UploadFile = File(...), 
    user_id: str = Form(...), 
    background_tasks: BackgroundTasks = None
):
    temp_filename = f"temp_login_{user_id.replace('@','_')}.wav"
    try:
        content = await file.read()
        with open(temp_filename, "wb") as buffer:
            buffer.write(content)
        
        normalize_audio(temp_filename)
        is_match, score = voice_security.verify_user(user_id, temp_filename)
        
        if is_match:
            if background_tasks:
                background_tasks.add_task(deep_sync_gmail, user_id, 20)
            return {"status": "success", "message": "Voice Verified", "confidence": float(score), "user_id": user_id}
        else:
            raise HTTPException(status_code=401, detail="Voice not recognized.")
    finally:
        if os.path.exists(temp_filename): os.remove(temp_filename)