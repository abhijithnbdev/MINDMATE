

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:permission_handler/permission_handler.dart';
import 'services/background_service.dart';
import 'main_layout.dart';
import 'features/auth/screens/login_screen.dart';
import 'core/theme/app_theme.dart';

// 🟢 Service and permissions remain

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await _requestPermissions();
  await initializeService();

  SharedPreferences prefs = await SharedPreferences.getInstance();
  final bool isLoggedIn = prefs.getBool('isLoggedIn') ?? false;
  final String? userId = prefs.getString('user_id');

  runApp(MyApp(isLoggedIn: isLoggedIn, userId: userId));
}

Future<void> _requestPermissions() async {
  await Permission.microphone.request();
  await Permission.notification.request();
}

class MyApp extends StatelessWidget {
  final bool isLoggedIn;
  final String? userId;
  const MyApp({super.key, required this.isLoggedIn, required this.userId});

  @override
  Widget build(BuildContext context) {
    SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ));

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'MindMate',
      theme: AppTheme.darkTheme,
      home: isLoggedIn && userId != null 
        ? MainLayout(userId: userId!) 
        : const LoginScreen(),
    );
  }
}
