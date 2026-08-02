import 'package:flutter/material.dart';
import 'screens/login_flow.dart';

void main() {
  runApp(const WayTransitApp());
}

class WayTransitApp extends StatelessWidget {
  const WayTransitApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WAY Transit',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF5974FF),
          primary: const Color(0xFF5974FF),
          background: const Color(0xFFF8F9FE),
        ),
        scaffoldBackgroundColor: const Color(0xFFF8F9FE),
        useMaterial3: true,
        // Since we don't have the custom Satoshi font installed, 
        // we'll rely on the default sans-serif (Roboto on Android, SF on iOS) 
        // which gives a clean look.
      ),
      home: const LoginFlow(),
    );
  }
}
