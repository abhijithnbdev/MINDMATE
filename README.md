# frontend

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

## to run flutter

cd frontend
flutter emulator

## find the emulator

flutter emulators --launch Pixel_6    

## to run backedn

 uvicorn app.main:app --reload           

uvicorn main:app --reload --host 0.0.0.0 --port 8000        



  Core Features:

Cognitive Brain: Integration with Ollama (Phi-3) for context-aware assistant responses.

Lifestyle Prediction: Random Forest Classifier (habit_model.pkl) trained on daily routines to predict user activities.

RAG System: Real-time retrieval of notes and schedules from SQLite to provide factual answers.

Voice Intelligence: Whisper-based STT for hands-free interaction.


psql -U postgres -d mindmate
password - postgres123