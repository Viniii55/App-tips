import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class VanguardTheme {
  // Private constructor to prevent instantiation
  VanguardTheme._();

  // Color Palette (Cyber-Dark)
  static const Color _background = Color(0xFF0F172A); // Slate 900
  static const Color _surface = Color(0xFF1E293B);    // Slate 800
  static const Color _primary = Color(0xFF8B5CF6);    // Violet 500
  static const Color _secondary = Color(0xFF10B981);  // Emerald 500 (Success)
  static const Color _error = Color(0xFFEF4444);      // Red 500
  static const Color _onBackground = Color(0xFFF8FAFC); // Slate 50

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: _background,
      primaryColor: _primary,
      
      colorScheme: const ColorScheme.dark(
        primary: _primary,
        secondary: _secondary,
        surface: _surface,
        background: _background,
        error: _error,
        onBackground: _onBackground,
        onSurface: _onBackground,
      ),

      // Typography
      textTheme: GoogleFonts.interTextTheme(
        ThemeData.dark().textTheme,
      ).apply(
        bodyColor: _onBackground,
        displayColor: _onBackground,
      ),

      // Card Theme
      cardTheme: CardTheme(
        color: _surface,
        elevation: 8,
        shadowColor: Colors.black26,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: _onBackground.withOpacity(0.05)),
        ),
      ),

      // Input Decoration (Forms)
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: _surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: _onBackground.withOpacity(0.1)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: _primary, width: 2),
        ),
        labelStyle: TextStyle(color: _onBackground.withOpacity(0.6)),
      ),

      // Button Theme
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: _primary,
          foregroundColor: Colors.white,
          elevation: 4,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontWeight: FontWeight.bold,
            letterSpacing: 1.0,
          ),
        ),
      ),
    );
  }
}
