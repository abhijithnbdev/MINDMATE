import os
import json
import base64
import pickle
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import requests
import re

# Standardized DB Router
from services.db_helper import save_to_appropriate_table

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def get_gmail_service(user_id):
    """Authenticates based on specific user_id to prevent data leakage."""
    creds = None
    token_dir = 'tokens'
    token_path = os.path.join(token_dir, f'token_{user_id}.pickle')
    
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Ensure credentials.json is in your root backend folder
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def call_llm_json(prompt):
    """Forces Ollama into JSON mode and cleans output."""
    OLLAMA_URL = "http://localhost:11434/api/generate"
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": "phi3", 
                "prompt": prompt, 
                "format": "json", 
                "stream": False
            },
            timeout=45
        )
        response_text = r.json().get("response", "").strip()
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            # Clean up potential trailing commas before closing braces
            cleaned_json = re.sub(r',\s*\}', '}', match.group(0))
            return json.loads(cleaned_json)
        return {"has_data": False}
    except Exception as e:
        print(f"⚠️ JSON Parse Fail: {e}")
        return {"has_data": False}

def deep_sync_gmail(user_id, count=50):
    """Scans emails and populates DB with strict date enforcement."""
    print(f"🕵️ MindMate is performing a deep sync for {user_id}...")
    try:
        service = get_gmail_service(user_id)
        results = service.users().messages().list(userId='me', maxResults=count).execute()
        messages = results.get('messages', [])
        
        # Current time for the AI to use as a fallback reference
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            snippet = msg.get('snippet', '').replace('"', "'") 
            
            prompt = f"""
            Extract info from email: "{snippet}"
            Reference Time: {now_str}
            
            Rules:
            1. Return JSON ONLY.
            2. If an event is found, "date" MUST be in 'YYYY-MM-DD HH:MM:00' format.
            3. NEVER use placeholders like 'current_date'. If unknown, use '{now_str}'.
            
            Schema:
            {{
              "has_data": true,
              "type": "event" | "note" | "task",
              "data": {{ 
                "title": "Short Heading", 
                "content": "Description", 
                "date": "{now_str}", 
                "location": "Kerala", 
                "link": "none" 
              }}
            }}
            """
            analysis = call_llm_json(prompt)
            if analysis and analysis.get("has_data"):
                save_to_appropriate_table(user_id, analysis, origin_location="Gmail")
                
        print(f"✅ Deep sync complete for {user_id}.")
    except Exception as e:
        print(f"❌ Sync Failed for {user_id}: {e}")

def send_gmail_message(user_id, recipient_email, subject, body):
    """Sends an email using the specific user's credentials."""
    service = get_gmail_service(user_id)
    message = MIMEText(body)
    message['to'] = recipient_email
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return f"✅ Email sent successfully."
    except Exception as e:
        return f"❌ Failed to send: {str(e)}"