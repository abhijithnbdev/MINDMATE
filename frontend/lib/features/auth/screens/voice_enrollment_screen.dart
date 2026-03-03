import 'dart:io';
import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/api_constants.dart';
import '../widgets/waveform_visualizer.dart';

class VoiceEnrollmentScreen extends StatefulWidget {
  final String userId;
  const VoiceEnrollmentScreen({super.key, required this.userId});

  @override
  State<VoiceEnrollmentScreen> createState() => _VoiceEnrollmentScreenState();
}

class _VoiceEnrollmentScreenState extends State<VoiceEnrollmentScreen> {
  final AudioRecorder _recorder = AudioRecorder();
  bool isRecording = false;
  bool isProcessing = false;
  String statusText = "Hold the button and say:\n\"My voice is my password\"";

  Future<void> _startRecording() async {
    final tempDir = await getTemporaryDirectory();
    final path = '${tempDir.path}/enroll.m4a';
    await _recorder.start(const RecordConfig(), path: path);
    setState(() {
      isRecording = true;
      statusText = "Listening...";
    });
  }

  Future<void> _stopAndUpload() async {
    final path = await _recorder.stop();
    setState(() {
      isRecording = false;
      isProcessing = true;
      statusText = "Creating Voice Signature...";
    });

    if (path != null) {
      // Upload to Backend
      var request = http.MultipartRequest('POST', Uri.parse(ApiConstants.voiceEnrollEndpoint));
      request.fields['user_id'] = widget.userId;
      request.files.add(await http.MultipartFile.fromPath('file', path));

      try {
        var response = await request.send();
        if (response.statusCode == 200) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Voice Enrollment Successful!")));
            Navigator.pop(context); // Go back
          }
        } else {
           setState(() => statusText = "Failed. Try Again.");
        }
      } catch (e) {
        setState(() => statusText = "Connection Error");
      } finally {
        setState(() => isProcessing = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.kBackgroundDark,
      appBar: AppBar(title: const Text("Voice Security Setup")),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.record_voice_over, size: 80, color: Colors.white),
            const SizedBox(height: 30),
            Text(
              statusText,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontSize: 18),
            ),
            const SizedBox(height: 40),
            WaveformVisualizer(isActive: isRecording),
            const SizedBox(height: 40),
            GestureDetector(
              onLongPressStart: (_) => _startRecording(),
              onLongPressEnd: (_) => _stopAndUpload(),
              child: Container(
                height: 80, width: 80,
                decoration: BoxDecoration(
                  color: isRecording ? Colors.redAccent : AppTheme.kPrimaryTeal,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: (isRecording ? Colors.redAccent : AppTheme.kPrimaryTeal).withOpacity(0.4),
                      blurRadius: 20,
                      spreadRadius: 5
                    )
                  ]
                ),
                child: const Icon(Icons.mic, color: Colors.black, size: 32),
              ),
            ),
            const SizedBox(height: 20),
            const Text("Hold to Record", style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}
