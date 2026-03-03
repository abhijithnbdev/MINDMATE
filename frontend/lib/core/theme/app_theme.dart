import 'package:flutter/material.dart';

class AppTheme {
  // 🎨 Core Colors
  static const Color kBackgroundDark = Color(0xFF121212);
  static const Color kCardDark = Color(0xFF1E1E1E);
  static const Color kPrimaryTeal = Color(0xFF00E5FF);
  static const Color kAccentGreen = Color(0xFF00C853);
  static const Color kTextWhite = Color(0xFFFFFFFF);
  static const Color kTextGrey = Color(0xFFB3B3B3);
  static const Color textSecondary = kTextGrey;
  static const Color primaryMint = kAccentGreen;
  static const Color surface = kCardDark;
  static const BoxShadow glowBoxShadow = BoxShadow(
    color: kAccentGreen,
    blurRadius: 20,
    spreadRadius: 4,
  );

  // 🌈 Gradients
  static const LinearGradient mintGradient = LinearGradient(
    colors: [kPrimaryTeal, kAccentGreen],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient darkGradient = LinearGradient(
    colors: [Color(0xFF1E1E1E), Color(0xFF121212)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  // 🏗️ Theme Configuration
  static ThemeData get darkTheme {
    return ThemeData.dark().copyWith(
      scaffoldBackgroundColor: kBackgroundDark,
      primaryColor: kPrimaryTeal,
      colorScheme: const ColorScheme.dark(
        primary: kPrimaryTeal,
        secondary: kAccentGreen,
        surface: kCardDark,
        error: Colors.redAccent,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: kBackgroundDark,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: kTextWhite,
          fontSize: 20,
          fontWeight: FontWeight.w600,
        ),
        iconTheme: IconThemeData(color: kTextWhite),
      ),
      // Fixes potential button/text issues
      textTheme: const TextTheme(
        bodyLarge: TextStyle(color: kTextWhite),
        bodyMedium: TextStyle(color: kTextWhite),
      ),
    );
  }
}
