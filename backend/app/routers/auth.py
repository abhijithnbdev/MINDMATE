from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
import shutil
import os
from pydantic import BaseModel
from services.db import get_db
from services.voice_auth import voice_security, VOICE_DB_DIR
from services.gmail import deep_sync_gmail
from passlib.hash import bcrypt



router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- Models ---
class UserAuth(BaseModel):
    user_id: str
    password: str

class WakeWordUpdate(BaseModel):
    user_id: str
    wake_word: str

# --- Security Helpers ---SpeakerRecognition
def hash_password(pw):
    return bcrypt.hash(pw)

def verify_password(plain, stored):
    return bcrypt.verify(plain, stored)

# --- Standard Auth ---

@router.post("/signup")
async def signup(user: UserAuth):
    conn = get_db()
    cur = conn.cursor()
    try:
        # Check if user exists (Postgres syntax)
        cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user.user_id,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Username taken")
        
        # Hash and store
        hashed_pw = hash_password(user.password)
        cur.execute("INSERT INTO users (user_id, password) VALUES (%s, %s)", 
                    (user.user_id, hashed_pw))
        conn.commit()
        return {"status": "success", "message": "User created"}
    finally:
        cur.close()
        conn.close()

@router.post("/login")
async def login(user: UserAuth, background_tasks: BackgroundTasks):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id, password FROM users WHERE user_id = %s", (user.user_id,))
        row = cur.fetchone() # returns a tuple (user_id, password)
        
        if not row or not verify_password(user.password, row[1]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # 🔥 SMART FEATURE: Sync emails in the background after login
        # This classifies emails into notes/events without making the user wait
        background_tasks.add_task(deep_sync_gmail, user.user_id, 50)
        
        return {"status": "success", "user_id": user.user_id}
    finally:
        cur.close()
        conn.close()

@router.post("/set-wake-word")
async def set_wake_word(data: WakeWordUpdate):
    conn = get_db()
    cur = conn.cursor()
    try:
        clean_word = data.wake_word.strip().lower()
        cur.execute("UPDATE users SET wake_word = %s WHERE user_id = %s", (clean_word, data.user_id))
        conn.commit()
        return {"status": "success", "message": f"Wake word updated to '{clean_word}'"}
    finally:
        cur.close()
        conn.close()


@router.post("/enroll")
async def enroll_new_user(user_id: str = Form(...), file: UploadFile = File(...)):
    # 1. Save the file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # 2. Use your earlier working code to save the signature
    success = voice_security.enroll_user(user_id, temp_path)
    
    # 3. Cleanup
    os.remove(temp_path)
    
    if success:
        return {"status": "success", "message": f"Voice profile created for {user_id}"}
    return {"status": "error", "message": "Enrollment failed"}
# --- VOICE AUTH (MindMate Proprietary) ---

@router.post("/enroll-voice")
async def enroll_voice(file: UploadFile = File(...), user_id: str = Form(...)):
    temp_filename = f"temp_enroll_{user_id}.wav"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        voice_security.enroll_user(user_id, temp_filename)
        return {"status": "success", "message": "Voice Signature Saved."}
    finally:
        if os.path.exists(temp_filename): 
            os.remove(temp_filename)

@router.post("/login-voice")
async def login_with_voice(file: UploadFile = File(...), user_id: str = Form(...), background_tasks: BackgroundTasks = None):
    temp_filename = f"temp_login_{user_id}.wav"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        reference_path = os.path.join(VOICE_DB_DIR, f"{user_id}.wav")
        if not os.path.exists(reference_path):
            raise HTTPException(status_code=404, detail="Voice not enrolled")
            
        is_match, score = voice_security.verify_user(user_id, temp_filename)
        if is_match:
            # Also trigger email sync for voice login
            if background_tasks:
                background_tasks.add_task(sync_and_classify_emails, user_id)
            return {"status": "success", "message": "Voice Verified", "confidence": score, "user_id": user_id}
        else:
            raise HTTPException(status_code=401, detail=f"Voice not recognized. Score: {score:.2f}")
    finally:
        if os.path.exists(temp_filename): 
            os.remove(temp_filename)