import os
import asyncio
import psycopg2
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pgvector.psycopg2 import register_vector

# Import routers
from app.routers import auth, chat, memories, dashboard, reminders
from services.gmail import deep_sync_gmail
from models.trainer import run_weekly_retraining

# 🟢 PostgreSQL Connection Settings
PG_CONFIG = {
    "dbname": "mindmate",       # Matches the yellow cylinder in your image
    "user": "postgres",         # Use 'postgres' if you haven't created 'mindmate_user'
    "password": "postgres123",  # Your pgAdmin login password
    "host": "127.0.0.1",
    "port": 5432
}

def initialize_db():
    """Initializes tables and PGVector extension."""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        register_vector(conn)
        cursor = conn.cursor()
        
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                password_hash TEXT
            )
        """)
        # Reminders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
                message TEXT,
                trigger_time TIMESTAMP,
                status TEXT DEFAULT 'active',
                priority_level TEXT,
                priority INTEGER DEFAULT 2
            )
        """)
        
        # Notes/Memories Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
                title TEXT,
                summary TEXT,
                original_text TEXT,
                origin_location TEXT,
                embedding vector(384),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Events Table for Planner/Dashboard
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
                title TEXT,
                description TEXT,
                start_time TIMESTAMP,
                location_name TEXT,
                origin_location TEXT
            )
        """)

        # Timeline/Memories Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
                memory_type TEXT,
                title TEXT,
                content TEXT,
                confidence_score DOUBLE PRECISION,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ PostgreSQL Initialized successfully.")
    except Exception as e:
        print(f"❌ Database Startup Error: {e}")


async def monitor_new_emails_loop():
    """Background task: Syncs Gmail every 5 minutes."""
    user_id = "meanonymus87@gmail.com" 
    while True:
        try:
            print(f"🤖 Proactive Agent: Checking Gmail for {user_id}...")
            deep_sync_gmail(user_id, count=5)
        except Exception as e:
            print(f"❌ Gmail Monitor Error: {e}")
        await asyncio.sleep(300) 

async def schedule_retraining():
    """Background task: Retrains models every 7 days."""
    while True:
        try:
            print("🚀 Starting Weekly Synapse Refresh...")
            await run_weekly_retraining()
        except Exception as e:
            print(f"❌ Training Loop Error: {e}")
        await asyncio.sleep(604800) 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    initialize_db()
    email_task = asyncio.create_task(monitor_new_emails_loop())
    train_task = asyncio.create_task(schedule_retraining())
    print("🚀 All Proactive Background Tasks Started.")
    yield
    # --- SHUTDOWN ---
    email_task.cancel()
    train_task.cancel()
    print("🛑 Background tasks shut down.")

# 🟢 MOVED THIS DOWN: Now it knows what 'lifespan' is!
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛤️ ROUTE REGISTRATION
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(memories.router, prefix="/memories", tags=["Memories"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])

@app.get("/")
async def root():
    return {"message": "MindMate Backend Active", "ip": "192.168.1.34"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

