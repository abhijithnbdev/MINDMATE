import sys
import os
# Add current directory to path so imports work
sys.path.append(os.getcwd())

from app.nlp import generate_conversational_response

def test_ai_agent():
    USER_ID = "abhijith"
    
    print("--- 🧠 AI AGENT TEST CASE ---")

    # TEST 1: RETRIEVAL & SUMMARY
    print("\n📝 TEST 1: Requesting Summary of last 3 emails...")
    query_1 = "Can you summarize my last 3 emails?"
    response_1 = generate_conversational_response(USER_ID, query_1)
    print(f"AI Response:\n{response_1}")

    print("-" * 30)

    # TEST 2: SENDING EMAIL
    # Note: Ensure you use a real email you can check
    test_email = "forgotitsorry1@gmail.com" 
    print(f"\n📨 TEST 2: Commanding AI to send an email to {test_email}...")
    query_2 = f"Send email to {test_email} about reminding we should meet at next office time.'"
    response_2 = generate_conversational_response(USER_ID, query_2)
    print(f"AI Response: {response_2}")

if __name__ == "__main__":
    test_ai_agent()