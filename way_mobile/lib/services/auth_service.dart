import 'dart:async';
import 'dart:convert';

import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import 'package:firebase_auth_platform_interface/firebase_auth_platform_interface.dart' show FirebaseAuthPlatform;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_service.dart';
import '../models/user.dart' as app_user;

class AuthService {
  final ApiService _apiService;
  static const String _tokenKey = 'auth_token';
  static const String _userEmailKey = 'user_email';

  AuthService(this._apiService);

  late final GoogleSignIn _googleSignIn = GoogleSignIn(
    clientId: kIsWeb ? '229828182883-web.apps.googleusercontent.com' : null,
  );
  final firebase_auth.FirebaseAuth _firebaseAuth = firebase_auth.FirebaseAuth.instance;
  String? _verificationId;
  firebase_auth.ConfirmationResult? _webConfirmationResult;

  // Save token to local storage
  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    _apiService.setToken(token);
    print('✅ Token saved: ${token.substring(0, 20)}... (length: ${token.length})');
  }

  // Get token from local storage
  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    if (token != null) {
      print('📝 Token found in storage: ${token.substring(0, 20)}... (length: ${token.length})');
      if (_isTokenExpired(token)) {
        print('⏰ Token expired, logging out');
        await logout();
        return null;
      }
      _apiService.setToken(token);
      return token;
    }
    // Token not found in storage
    print('❌ No token in storage');
    _apiService.setToken(null);
    return null;
  }

  bool _isTokenExpired(String token) {
    try {
      final parts = token.split('.');
      if (parts.length != 3) return true;
      final payload = json.decode(utf8.decode(base64Url.decode(base64Url.normalize(parts[1]))));
      final exp = payload['exp'];
      if (exp is int) {
        return DateTime.fromMillisecondsSinceEpoch(exp * 1000).isBefore(DateTime.now());
      }
      return true;
    } catch (_) {
      return true;
    }
  }

  // Save user email
  Future<void> saveUserEmail(String email) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userEmailKey, email);
  }

  // Get user email
  Future<String?> getUserEmail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_userEmailKey);
  }

  // Login
  Future<Map<String, dynamic>> login(String email, String password) async {
    final result = await _apiService.login(email, password);
    final token = result['access_token'];
    await saveToken(token);
    await saveUserEmail(email);
    return result;
  }

  // Signup
  Future<app_user.User> signup(String email, String password) async {
    final user = await _apiService.signup(email, password);
    await saveUserEmail(email);
    return user;
  }

  // Logout
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userEmailKey);
    _apiService.setToken(null);
    try {
      await _googleSignIn.signOut();
    } catch (_) {}
    try {
      await _firebaseAuth.signOut();
    } catch (_) {}
  }

  // Check if user is logged in
  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null;
  }

  // Ensure token is loaded and API service is set
  // Returns true if logged in, false otherwise
  Future<bool> ensureAuthLoaded() async {
    final token = await getToken();
    if (token == null) {
      _apiService.setToken(null);
      return false;
    }
    _apiService.setToken(token);
    return true;
  }

  // Get current user
  Future<app_user.User> getCurrentUser() async {
    await getToken();
    return await _apiService.getCurrentUser();
  }

  // Sign in with Google (uses Firebase signInWithRedirect on Web, popup on Mobile)
  Future<void> signInWithGoogle() async {
    if (kIsWeb) {
      // ✅ FIX: Use signInWithRedirect instead of signInWithPopup
      // This is the modern, recommended approach for Flutter Web
      // Avoids Cross-Origin-Opener-Policy issues with popups
      final googleProvider = firebase_auth.GoogleAuthProvider();
      
      // Set custom parameters for better UX
      googleProvider.setCustomParameters({
        'prompt': 'select_account', // Always show account selection
      });
      
      try {
        await _firebaseAuth.signInWithRedirect(googleProvider);
        // After redirect, app will resume here
        // No need to manually navigate - listener will handle it
        return;
      } on firebase_auth.FirebaseAuthException catch (e) {
        // Handle Firebase auth errors
        print("Firebase Auth Error: ${e.code} - ${e.message}");
        rethrow;
      } catch (e) {
        print("Google sign-in error: $e");
        rethrow;
      }
    }

    // Mobile flow (unchanged)
    final GoogleSignInAccount? account = await _googleSignIn.signIn();
    if (account == null) throw Exception('Google sign-in aborted');

    final GoogleSignInAuthentication auth = await account.authentication;
    final String? idToken = auth.idToken;
    final String? accessToken = auth.accessToken;
    if (idToken == null || accessToken == null) {
      throw Exception('Missing Google authentication tokens');
    }

    final credential = firebase_auth.GoogleAuthProvider.credential(
      idToken: idToken,
      accessToken: accessToken,
    );

    await _firebaseAuth.signInWithCredential(credential);
    await _handleFirebaseSignIn(accountEmail: account.email);
  }

  // Phone OTP flow
  Future<void> requestPhoneOtp(String phone) async {
    if (kIsWeb) {
      try {
        // Omitting 'container' creates an invisible reCAPTCHA automatically.
        // This avoids the reCAPTCHA Enterprise warning and requires no visible widget.
        final recaptchaVerifier = firebase_auth.RecaptchaVerifier(
          auth: FirebaseAuthPlatform.instance,
          onSuccess: () {
            // ignore: avoid_print
            print('reCAPTCHA verified successfully');
          },
          onError: (error) {
            // ignore: avoid_print
            print('reCAPTCHA error: $error');
          },
          onExpired: () {
            // ignore: avoid_print
            print('reCAPTCHA expired');
          },
        );
        _webConfirmationResult = await _firebaseAuth.signInWithPhoneNumber(
          phone,
          recaptchaVerifier,
        );
        return;
      } on firebase_auth.FirebaseAuthException catch (e) {
        // ignore: avoid_print
        print("============ FIREBASE WEB ERROR ============");
        // ignore: avoid_print
        print("Firebase Error Code : ${e.code}");
        // ignore: avoid_print
        print("Firebase Message    : ${e.message}");
        // ignore: avoid_print
        print("============================================");
        rethrow;
      } catch (e) {
        // ignore: avoid_print
        print("Phone OTP request error: $e");
        rethrow;
      }
    }

    final completer = Completer<void>();

    await _firebaseAuth.verifyPhoneNumber(
      phoneNumber: phone,
      timeout: const Duration(seconds: 60),
      verificationCompleted: (firebase_auth.PhoneAuthCredential credential) async {
        try {
          await _firebaseAuth.signInWithCredential(credential);
          await _handleFirebaseSignIn();
          if (!completer.isCompleted) completer.complete();
        } catch (e) {
          if (!completer.isCompleted) completer.completeError(e);
        }
      },
      verificationFailed: (firebase_auth.FirebaseAuthException e) {
        // ignore: avoid_print
        print("============ FIREBASE MOBILE ERROR ============");
        // ignore: avoid_print
        print("Firebase Error Code : ${e.code}");
        // ignore: avoid_print
        print("Firebase Message    : ${e.message}");
        // ignore: avoid_print
        print("===============================================");
        if (!completer.isCompleted) completer.completeError(e);
      },
      codeSent: (String verificationId, int? resendToken) {
        _verificationId = verificationId;
        if (!completer.isCompleted) completer.complete();
      },
      codeAutoRetrievalTimeout: (String verificationId) {
        _verificationId = verificationId;
      },
    );

    return completer.future;
  }

  Future<void> verifyPhoneOtp(String phone, String otp) async {
    try {
      if (kIsWeb) {
        if (_webConfirmationResult == null) {
          throw Exception('Phone verification has not been initiated');
        }
        await _webConfirmationResult!.confirm(otp);
        await _handleFirebaseSignIn();
        return;
      }

      if (_verificationId == null) {
        throw Exception('Phone verification has not been initiated');
      }

      final credential = firebase_auth.PhoneAuthProvider.credential(
        verificationId: _verificationId!,
        smsCode: otp,
      );

      await _firebaseAuth.signInWithCredential(credential);
      await _handleFirebaseSignIn();
    } on firebase_auth.FirebaseAuthException catch (e) {
      // ignore: avoid_print
      print("============ FIREBASE VERIFY OTP ERROR ============");
      // ignore: avoid_print
      print("Firebase Error Code : ${e.code}");
      // ignore: avoid_print
      print("Firebase Message    : ${e.message}");
      // ignore: avoid_print
      print("====================================================");
      rethrow;
    } catch (e) {
      // ignore: avoid_print
      print("OTP verification error: $e");
      rethrow;
    }
  }

  Future<void> _handleFirebaseSignIn({String? accountEmail}) async {
    final firebase_auth.User? firebaseUser = _firebaseAuth.currentUser;
    if (firebaseUser == null) {
      throw Exception('Firebase authentication failed');
    }

    final String? idToken = await firebaseUser.getIdToken();
    if (idToken == null || idToken.isEmpty) {
      throw Exception('Firebase ID token not available');
    }

    print('🔐 Sending Firebase token to backend: ${idToken.substring(0, 20)}...');
    final resp = await _apiService.firebaseAuth(idToken);
    print('📦 Backend response: $resp');
    
    final token = resp['access_token'] as String?;
    if (token == null) {
      print('❌ Backend did not return access_token');
      throw Exception('Backend authentication failed');
    }

    print('🎉 Received access_token from backend: ${token.substring(0, 20)}...');
    await saveToken(token);
    await saveUserEmail(firebaseUser.email ?? accountEmail ?? firebaseUser.phoneNumber ?? '');
  }

  Future<app_user.User> updateProfileName(String name) async {
    final updatedUser = await _apiService.updateCurrentUser(name);
    return updatedUser;
  }

  Future<void> deleteAccount() async {
    await _apiService.deleteCurrentUser();
    await logout();
  }
}
