import 'dart:async';
import 'dart:convert';
import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

/// Models for AI Chat
class ChatMessage {
  final String id;
  final String content;
  final bool isUser;
  final DateTime timestamp;
  final MessageState state;
  final String? agentName;

  ChatMessage({
    required this.id,
    required this.content,
    required this.isUser,
    required this.timestamp,
    this.state = MessageState.delivered,
    this.agentName,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] as String? ?? DateTime.now().millisecondsSinceEpoch.toString(),
      content: json['content'] as String,
      isUser: json['is_user'] as bool? ?? false,
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'] as String)
          : DateTime.now(),
      state: MessageState.values.firstWhere(
        (e) => e.toString() == 'MessageState.${json['state'] as String? ?? 'delivered'}',
        orElse: () => MessageState.delivered,
      ),
      agentName: json['agent_name'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'content': content,
      'is_user': isUser,
      'timestamp': timestamp.toIso8601String(),
      'state': state.toString().split('.').last,
      'agent_name': agentName,
    };
  }

  ChatMessage copyWith({
    String? id,
    String? content,
    bool? isUser,
    DateTime? timestamp,
    MessageState? state,
    String? agentName,
  }) {
    return ChatMessage(
      id: id ?? this.id,
      content: content ?? this.content,
      isUser: isUser ?? this.isUser,
      timestamp: timestamp ?? this.timestamp,
      state: state ?? this.state,
      agentName: agentName ?? this.agentName,
    );
  }
}

enum MessageState { sending, delivered, failed }

class AIChatRequest {
  final String message;
  final String? userId;
  final String? sessionId;

  AIChatRequest({required this.message, this.userId, this.sessionId});

  Map<String, dynamic> toJson() {
    return {
      'message': message,
      if (userId != null) 'user_id': userId,
      if (sessionId != null) 'session_id': sessionId,
    };
  }
}

class AIChatResponse {
  final String response;
  final String agent;

  AIChatResponse({required this.response, required this.agent});

  factory AIChatResponse.fromJson(Map<String, dynamic> json) {
    return AIChatResponse(
      response: json['response'] as String? ?? '',
      agent: json['agent'] as String? ?? 'Unknown',
    );
  }
}

/// Exception types for AI Chat
class AIChatException implements Exception {
  final String message;
  final AIChatErrorType type;

  AIChatException({required this.message, required this.type});

  @override
  String toString() => 'AIChatException: $message (${type.toString()})';
}

enum AIChatErrorType {
  networkError,
  timeout,
  serverError,
  invalidResponse,
  authenticationFailed,
  unknown,
}

/// AI Chat Service
class AIChatService {
  final String _baseUrl;
  String? _authToken;
  static const int _timeoutSeconds = 30;

  AIChatService({String? baseUrl, String? authToken})
    : _baseUrl = baseUrl ?? ApiConfig.agentBaseUrl,
      _authToken = authToken;

  /// Update the auth token
  void setAuthToken(String? token) {
    _authToken = token;
  }

  /// Get Firebase ID token from current user if available
  Future<String?> _getFirebaseToken() async {
    try {
      final user = firebase_auth.FirebaseAuth.instance.currentUser;
      if (user != null) {
        return await user.getIdToken();
      }
    } catch (_) {
      // Silently fail if token cannot be retrieved
    }
    return null;
  }

  Map<String, String> get _headers {
    final headers = {'Content-Type': 'application/json'};
    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  /// Send a message to the AI agent
  Future<AIChatResponse> sendMessage({
    required String message,
    String? userId,
    String? sessionId,
  }) async {
    if (message.trim().isEmpty) {
      throw AIChatException(
        message: 'Message cannot be empty',
        type: AIChatErrorType.invalidResponse,
      );
    }

    // Ensure we have a fresh token
    final token = await _getFirebaseToken();
    if (token != null) {
      _authToken = token;
    }

    final request = AIChatRequest(message: message, userId: userId, sessionId: sessionId);

    try {
      final uri = Uri.parse('$_baseUrl/chat');
      final response = await http
          .post(uri, headers: _headers, body: jsonEncode(request.toJson()))
          .timeout(
            const Duration(seconds: _timeoutSeconds),
            onTimeout: () {
              throw AIChatException(
                message: 'Request timeout after $_timeoutSeconds seconds',
                type: AIChatErrorType.timeout,
              );
            },
          );

      return _handleResponse(response);
    } on AIChatException {
      rethrow;
    } catch (e) {
      throw AIChatException(
        message: 'Network error: ${e.toString()}',
        type: AIChatErrorType.networkError,
      );
    }
  }

  /// Health check
  Future<bool> checkHealth() async {
    try {
      final uri = Uri.parse('$_baseUrl/health');
      final response = await http
          .get(
            uri,
            headers: {'Content-Type': 'application/json'},
          )
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  AIChatResponse _handleResponse(http.Response response) {
    try {
      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return AIChatResponse.fromJson(json);
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        throw AIChatException(
          message: 'Authentication failed. Please log in again.',
          type: AIChatErrorType.authenticationFailed,
        );
      } else if (response.statusCode >= 500) {
        throw AIChatException(
          message: 'Server error (${response.statusCode}). Please try again later.',
          type: AIChatErrorType.serverError,
        );
      } else {
        throw AIChatException(
          message: 'Unexpected response (${response.statusCode}): ${response.body}',
          type: AIChatErrorType.invalidResponse,
        );
      }
    } on AIChatException {
      rethrow;
    } catch (e) {
      throw AIChatException(
        message: 'Failed to parse response: ${e.toString()}',
        type: AIChatErrorType.invalidResponse,
      );
    }
  }
}
