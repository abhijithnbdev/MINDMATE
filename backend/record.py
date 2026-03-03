import sounddevice as sd
from scipy.io.wavfile import write
import time

def record_audio(filename, duration):
    fs = 16000  # Optimal sample rate for SpeechBrain
    print(f"\n🎙️  Recording '{filename}' for {duration} seconds...")
    print("🔴 SPEAK NOW!")
    
    # Record mono audio
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    
    write(filename, fs, recording)
    print(f"✅ Saved: {filename}")

if __name__ == "__main__":
    print("--- MINDMATE VOICE RECORDER ---")
    
    # 1. Record Enrollment (Your master signature)
    input("Press Enter to record your ENROLLMENT (Signature) - 5 Seconds...")
    record_audio("my_voice_enroll.wav", 5)
    
    # 2. Record Login (Your verification attempt)
    input("\nPress Enter to record your LOGIN attempt - 5 Seconds...")
    record_audio("my_voice_login.wav", 5)
    
    print("\n🎉 Files ready! Now run 'python test_voice.py'")