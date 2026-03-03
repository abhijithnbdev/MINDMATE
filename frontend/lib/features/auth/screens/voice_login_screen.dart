import 'dart:io';
import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/api_constants.dart';
import '../../../main_layout.dart';

class VoiceLoginScreen extends StatefulWidget {
  const VoiceLoginScreen({super.key});
  @override
  State<VoiceLoginScreen> createState() => _VoiceLoginScreenState();
}

class _VoiceLoginScreenState extends State<VoiceLoginScreen> {
  final AudioRecorder _recorder = AudioRecorder();
  final TextEditingController _userController = TextEditingController();
  bool isRecording = false;
  bool isProcessing = false;
  String statusText = "Hold and speak your passphrase";

  Future<void> _startRecording() async {
    final tempDir = await getTemporaryDirectory();
    final path = '${tempDir.path}/login_voice.m4a';
    await _recorder.start(const RecordConfig(), path: path);
    setState(() {
      isRecording = true;
      statusText = "Listening...";
    });
  }

  Future<void> _stopAndLogin() async {
    final path = await _recorder.stop();
    setState(() {
      isRecording = false;
      isProcessing = true;
      statusText = "Verifying...";
    });

    final userId = _userController.text.trim();
    if (path != null && userId.isNotEmpty) {
      var request = http.MultipartRequest('POST', Uri.parse(ApiConstants.voiceLoginEndpoint));
      request.fields['user_id'] = userId;
      request.files.add(await http.MultipartFile.fromPath('file', path));

      try {
        var response = await request.send();
        if (response.statusCode == 200) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setBool('isLoggedIn', true);
          await prefs.setString('user_id', userId);
          if (mounted) {
            Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (_) => MainLayout(userId: userId)),
              (route) => false,
            );
          }
        } else if (response.statusCode == 404) {
          setState(() => statusText = "Voice not enrolled");
          if (mounted) {
            Navigator.push(context, MaterialPageRoute(builder: (_) => VoiceEnrollmentScreen(userId: userId)));
          }
        } else {
          setState(() => statusText = "Not recognized");
        }
      } catch (_) {
        setState(() => statusText = "Connection error");
      } finally {
        setState(() => isProcessing = false);
      }
    } else {
      setState(() {
        isProcessing = false;
        statusText = "Enter username";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.kBackgroundDark,
      appBar: AppBar(title: const Text("Voice Login")),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            TextField(
              controller: _userController,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                filled: true,
                fillColor: AppTheme.surface,
                labelText: "Username",
                labelStyle: const TextStyle(color: AppTheme.textSecondary),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              ),
            ),
            const SizedBox(height: 24),
            Container(
              height: 80,
              width: 80,
              decoration: BoxDecoration(
                color: isRecording ? Colors.redAccent : AppTheme.kPrimaryTeal,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: (isRecording ? Colors.redAccent : AppTheme.kPrimaryTeal).withOpacity(0.4),
                    blurRadius: 20,
                    spreadRadius: 5,
                  )
                ],
              ),
              child: GestureDetector(
                onLongPressStart: (_) => _startRecording(),
                onLongPressEnd: (_) => _stopAndLogin(),
                child: const Icon(Icons.mic, color: Colors.black, size: 32),
              ),
            ),
            const SizedBox(height: 20),
            Text(statusText, style: const TextStyle(color: Colors.white70)),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: isProcessing ? null : () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryMint,
                  foregroundColor: Colors.black,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text("Back"),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
