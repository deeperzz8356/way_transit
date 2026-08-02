import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';
import '../models/user.dart';

class AuthService {
  final ApiService _apiService;
  static const String _tokenKey = 'auth_token';
  static const String _userEmailKey = 'user_email';

  AuthService(this._apiService);

  // Save token to local storage
  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    _apiService.setToken(token);
  }

  // Get token from local storage
  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    if (token != null) {
      _apiService.setToken(token);
    }
    return token;
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
  Future<User> signup(String email, String password) async {
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
  }

  // Check if user is logged in
  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null;
  }

  // Get current user
  Future<User> getCurrentUser() async {
    return await _apiService.getCurrentUser();
  }
}
