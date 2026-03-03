class ApiConstants {
  // Use 10.0.2.2 for Android Emulator, localhost for iOS Simulator
  // static const String baseUrl = "http://10.0.2.2:8000";
  static const String baseUrl = "http://192.168.1.33:8000";
  
  // Auth
  static const String login = "$baseUrl/auth/login";
  static const String signup = "$baseUrl/auth/signup";
  static const String loginEndpoint = login;
  static const String voiceEnroll = "$baseUrl/auth/enroll-voice";
  static const String voiceLogin = "$baseUrl/auth/login-voice";
  static const String voiceEnrollEndpoint = voiceEnroll;
  static const String voiceLoginEndpoint = voiceLogin;
  
  // Chat & Voice
  static const String chatSend = "$baseUrl/chat/send";
  static const String chatHistory = "$baseUrl/chat/history";
  static const String uploadAudio = "$baseUrl/chat/upload-audio"; // The new endpoint
  static const String chatEndpoint = chatSend;
  static const String chatHistoryEndpoint = chatHistory;
  static const String uploadAudioEndpoint = uploadAudio;
  
  // Data
  static const String dashboard = "$baseUrl/dashboard";
  static const String dashboardEndpoint = dashboard;
  static const String memories = "$baseUrl/memories"; // Note: You might need to add this route to backend if missing, or use /chat/history with filters
  static const String memoriesEndpoint = memories;
  static const String predict = "$baseUrl/predict"; // If you implement the prediction endpoint
  static const String predictScheduleEndpoint = "$baseUrl/predict/schedule";
  static const String analyticsPeriodEndpoint = "$baseUrl/analytics/period";
}
