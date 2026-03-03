import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart'; 

import '../../../core/constants/api_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../widgets/glowing_orb.dart';

class HomeOrbScreen extends StatefulWidget {
  final String userId;
  const HomeOrbScreen({super.key, required this.userId});

  @override
  State<HomeOrbScreen> createState() => _HomeOrbScreenState();
}

class _HomeOrbScreenState extends State<HomeOrbScreen> {
  // --- STATE ---
  bool _isListening = false;  // Mic is ON
  bool _isProcessing = false; // Sending to AI
  
  // Data
  String _userTranscript = ""; 
  String _aiResponse = "";
  
  // Tools
  final TextEditingController _textController = TextEditingController();
  late final AudioRecorder _audioRecorder;

  @override
  void initState() {
    super.initState();
    _audioRecorder = AudioRecorder();
  }

  @override
  void dispose() {
    _audioRecorder.dispose();
    _textController.dispose();
    super.dispose();
  }

  // --- 🧠 DYNAMIC STATUS TEXT ---
  // This ensures the label is ALWAYS correct based on the state
  String get _currentStatus {
    if (_isListening) return "LISTENING...";
    if (_isProcessing) return "THINKING...";
    if (_aiResponse.isNotEmpty) return "ACTIVE";
    return "TAP ORB TO SPEAK";
  }

  Color get _statusColor {
    if (_isListening) return AppTheme.primaryMint;
    if (_isProcessing) return Colors.amber;
    return Colors.white54;
  }

  // --- 🎤 SAFE RECORDING LOGIC ---

  Future<void> _toggleRecording() async {
    if (_isListening) {
      await _stopRecording();
    } else {
      await _startRecording();
    }
  }

  Future<void> _startRecording() async {
    try {
      if (await _audioRecorder.hasPermission()) {
        final Directory appDir = await getApplicationDocumentsDirectory();
        final String filePath = '${appDir.path}/temp_command.m4a';
        
        // Config optimized for Android Emulator
        const config = RecordConfig(
          encoder: AudioEncoder.aacLc, 
          bitRate: 128000,
          sampleRate: 44100,
        );
        
        // 1. Start Recording
        await _audioRecorder.start(config, path: filePath);
        
        // 2. Update UI only AFTER start succeeds
        setState(() {
          _isListening = true;
          _isProcessing = false;
          _userTranscript = "";
          _aiResponse = "";
        });
        
        print("🎤 Recorder Started Successfully");
      }
    } catch (e) {
      print("❌ Start Error: $e");
      setState(() => _isListening = false);
    }
  }

  Future<void> _stopRecording() async {
    try {
      // 🛡️ SAFETY CHECK: Is it actually recording?
      // This prevents the "MPEG4Writer" crash if you tap too fast.
      final bool isRecording = await _audioRecorder.isRecording();
      
      if (!isRecording) {
        print("⚠️ Ignored Stop: Recorder was not running.");
        setState(() => _isListening = false);
        return;
      }

      // 1. Stop Recording
      final path = await _audioRecorder.stop();
      print("✅ Recorder Stopped. File saved at: $path");
      
      // 2. Update UI
      setState(() {
        _isListening = false;
        _isProcessing = true; // Show THINKING...
      });

      // 3. Send to Backend
      if (path != null) {
        final transcript = await _uploadAudioFile(path);
        
        if (transcript != null && transcript.isNotEmpty) {
          setState(() => _userTranscript = transcript);
          await _sendTextToBrain(transcript);
        } else {
           setState(() {
             _isProcessing = false;
             _aiResponse = "I couldn't hear you.";
           });
        }
      }
    } catch (e) {
      print("❌ Stop Error: $e");
      setState(() {
        _isListening = false;
        _isProcessing = false;
      });
    }
  }

  

  // --- 🌐 API CALLS ---
  Future<String?> _uploadAudioFile(String filePath) async {
    try {
      var request = http.MultipartRequest('POST', Uri.parse(ApiConstants.uploadAudioEndpoint));
      request.fields['user_id'] = widget.userId;
      request.files.add(await http.MultipartFile.fromPath('file', filePath));
      
      var response = await request.send();
      var responseData = await http.Response.fromStream(response);
      var data = jsonDecode(responseData.body);

      return data['transcript'];
    } catch (e) {
      return null;
    }
  }

  Future<void> _sendTextToBrain(String text) async {
    try {
      final response = await http.post(
        Uri.parse(ApiConstants.chatEndpoint),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"user_id": widget.userId, "text": text}),
      );

      final data = jsonDecode(response.body);
      
      if (mounted) {
        setState(() {
          _isProcessing = false; // AI Done
          
          if (data['status'] == 'ignored') {
            _aiResponse = "(Ignored)";
          } else if (data['status'] == 'passive_save') {
            _aiResponse = "✅ Saved silently.";
          } else {
            _aiResponse = data['ai_response'] ?? "Done.";
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isProcessing = false;
          _aiResponse = "Connection Error";
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(0, -0.2),
            radius: 1.3,
            colors: [Color(0xFF1A222C), Color(0xFF0D1117)],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.only(bottom: 20),
            physics: const BouncingScrollPhysics(),
            child: Column(
            children: [
              // --- HEADER ---
              Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Icon(Icons.history, color: Colors.white54),
                    
                    // 🟢 DYNAMIC STATUS DISPLAY
                    Text(
                      _currentStatus, 
                      style: TextStyle(
                        color: _statusColor,
                        letterSpacing: 2,
                        fontWeight: FontWeight.bold,
                        fontSize: 14
                      ),
                    ),
                    
                    const Icon(Icons.settings, color: Colors.white54),
                  ],
                ),
              ),
              
              // --- MAIN ORB ---
              GestureDetector(
                onTap: _toggleRecording,
                child: GlowingOrb(
                  // Motion only when speak enabled (recording)
                  isListening: _isListening,
                  size: MediaQuery.of(context).size.width * 0.7,
                ),
              ),
              
              const SizedBox(height: 30),
              
              Text(
                _isListening ? "Tap to Stop" : "Tap to Speak", 
                style: const TextStyle(color: Colors.white24)
              ),

              const SizedBox(height: 20),

              // --- TRANSCRIPT CARD ---
              if (_userTranscript.isNotEmpty || _aiResponse.isNotEmpty)
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.symmetric(horizontal: 30),
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white10),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // User Text
                      if (_userTranscript.isNotEmpty)
                        Align(
                          alignment: Alignment.centerRight,
                          child: Text(
                            '"$_userTranscript"',
                            style: const TextStyle(color: Colors.white70, fontStyle: FontStyle.italic),
                          ),
                        ),
                      
                      if (_userTranscript.isNotEmpty && _aiResponse.isNotEmpty)
                        const Divider(color: Colors.white10, height: 20),

                      // AI Text
                      if (_aiResponse.isNotEmpty)
                        Text(
                          _aiResponse,
                          style: const TextStyle(color: AppTheme.primaryMint, fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                    ],
                  ),
                ),

              // --- TEXT INPUT (Keyboard) ---
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 20),
                child: TextField(
                  controller: _textController,
                  style: const TextStyle(color: Colors.white),
                  // When typing, we mimic the logic without the mic
                  onSubmitted: (text) {
                     setState(() {
                       _userTranscript = text;
                       _isProcessing = true; // Show thinking
                     });
                    _sendTextToBrain(text);
                    _textController.clear();
                  },
                  decoration: InputDecoration(
                    hintText: "Or type a command...",
                    hintStyle: const TextStyle(color: Colors.white30),
                    filled: true,
                    fillColor: Colors.black26,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(30), borderSide: BorderSide.none),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.send, color: AppTheme.primaryMint),
                      onPressed: () {
                         setState(() {
                           _userTranscript = _textController.text;
                           _isProcessing = true;
                         });
                        _sendTextToBrain(_textController.text);
                        _textController.clear();
                      },
                    ),
                  ),
                ),
              ),
            ],
            ),
          ),
        ),
      ),
    );
  }
}
