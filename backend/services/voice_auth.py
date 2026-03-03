import os
import shutil
import torch
import torchaudio
import soundfile as sf
import numpy as np

# --- 🛠️ STEP 1: PATCHES ---
import huggingface_hub
# We tell the library to ONLY look at local files
os.environ["HF_HUB_OFFLINE"] = "1" 

if not hasattr(torchaudio, "list_audio_backends"):
    torchaudio.list_audio_backends = lambda: ["soundfile"]

from speechbrain.inference.speaker import SpeakerRecognition

# --- 🛠️ STEP 2: PATH CONFIG ---
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_DB_DIR = os.path.join(BACKEND_DIR, "voice_signatures")
# This must point to the folder containing your .ckpt and .yaml files
LOCAL_MODEL_DIR = os.path.join(BACKEND_DIR, "voice_auth_model")

os.makedirs(VOICE_DB_DIR, exist_ok=True)

class VoiceAuthenticator:
    def __init__(self):
        print("🔒 Loading Voice Security Model (OFFLINE MODE)...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # We removed local_files_only=True because HF_HUB_OFFLINE handles it
        self.verification_model = SpeakerRecognition.from_hparams(
            source=LOCAL_MODEL_DIR, 
            savedir=LOCAL_MODEL_DIR, 
            run_opts={"device": self.device}
        )
        print("✅ Voice Security Model Loaded from Local Storage.")

    def enroll_user(self, user_id: str, audio_path: str):
        user_signature_path = os.path.join(VOICE_DB_DIR, f"{user_id}.wav")
        shutil.copy(audio_path, user_signature_path)
        return True

    def _manual_load(self, path):
        data, samplerate = sf.read(path)
        tensor = torch.from_numpy(data).float()
        if len(tensor.shape) > 1:
            tensor = tensor[:, 0]
        return tensor.unsqueeze(0).to(self.device)

    def verify_user(self, user_id: str, input_audio_path: str):
        reference_path = os.path.join(VOICE_DB_DIR, f"{user_id}.wav")
        if not os.path.exists(reference_path):
            return False, 0.0 
        try:
            ref_wav = self._manual_load(reference_path)
            in_wav = self._manual_load(input_audio_path)
            score, prediction = self.verification_model.verify_batch(ref_wav, in_wav)
            return bool(prediction[0]), float(score[0])
        except Exception as e:
            print(f"❌ Verification Error: {e}")
            return False, 0.0

voice_security = VoiceAuthenticator()