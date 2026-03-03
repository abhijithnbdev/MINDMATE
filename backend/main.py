import os
import asyncio
import psycopg2
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pgvector.psycopg2 import register_vector

# Import your own routers and services
from app.routers import auth, chat, memories, dashboard
from services.gmail import deep_sync_gmail

# 🟢 PostgreSQL Connection Settings
PG_CONFIG = {
    "dbname": "mindmate",
    "user": "mindmate_user",
    "password": "mindmate123",
    "host": "127.0.0.1",
    "port": 5432
}

# 🤖 BACKGROUND MONITORING (The Native Way)
async def monitor_new_emails_loop():
    """Replaces @repeat_every. Checks Gmail every 5 mins."""
    while True:
        try:
            print("🤖 Proactive Agent: Checking Gmail for updates...")
            # Using meanonymus87@gmail.com as we discussed
            user_id = "meanonymus87@gmail.com" 
            deep_sync_gmail(user_id, count=5)
        except Exception as e:
            print(f"❌ Monitor Loop Error: {e}")
        
        await asyncio.sleep(300) # Wait 5 minutes

# 🚀 LIFESPAN MANAGER
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    initialize_db()
    # Start the email monitor in the background
    monitor_task = asyncio.create_task(monitor_new_emails_loop())
    yield
    # --- Shutdown ---
    monitor_task.cancel()

app = FastAPI(title="MindMate API", lifespan=lifespan)

# 🟢 CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(memories.router)
app.include_router(dashboard.router)

def initialize_db():
    """Initializes the database and defines 'cursor' locally."""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        register_vector(conn)
        
        # 🔑 THIS IS THE LINE THAT DEFINES 'cursor'
        cursor = conn.cursor()
        
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY, 
                password TEXT
            )
        """)
        
        # Create Events Table with ON DELETE CASCADE
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

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ PostgreSQL Initialized successfully.")
    except Exception as e:
        print(f"❌ Database Startup Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)