import requests

BASE_URL = "http://localhost:8000"
USER_ID = "abhijith" # Your test user ID

def run_voice_test():
    # 1. TEST ENROLLMENT
    print(f"🚀 Step 1: Enrolling Voice for {USER_ID}...")
    try:
        with open("my_voice_enroll.wav", "rb") as f:
            files = {"file": ("enroll.wav", f, "audio/wav")}
            data = {"user_id": USER_ID}
            response = requests.post(f"{BASE_URL}/auth/enroll-voice", files=files, data=data)
            print("Response:", response.json())
    except FileNotFoundError:
        print("❌ Error: my_voice_enroll.wav not found. Run record.py first.")
        return

    # 2. TEST LOGIN/VERIFICATION
    print(f"\n🚀 Step 2: Attempting Voice Login for {USER_ID}...")
    try:
        with open("my_voice_login.wav", "rb") as f:
            files = {"file": ("login.wav", f, "audio/wav")}
            data = {"user_id": USER_ID}
            response = requests.post(f"{BASE_URL}/auth/login-voice", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS! Match: {result['status']}")
                print(f"📊 Confidence Score: {result['confidence']:.4f}")
            else:
                print(f"❌ FAILED: {response.json()['detail']}")
    except FileNotFoundError:
        print("❌ Error: my_voice_login.wav not found.")

if __name__ == "__main__":
    run_voice_test()