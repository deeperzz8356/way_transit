/// Represents a single message in the chat conversation
class ChatMessageModel {
  final String id;
  final String content;
  final bool isUser;
  final DateTime timestamp;
  final MessageState state;
  final String? agentName;

  ChatMessageModel({
    required this.id,
    required this.content,
    required this.isUser,
    required this.timestamp,
    this.state = MessageState.delivered,
    this.agentName,
  });

  /// Create a new user message
  factory ChatMessageModel.user({required String content, String? id, DateTime? timestamp}) {
    return ChatMessageModel(
      id: id ?? DateTime.now().millisecondsSinceEpoch.toString(),
      content: content,
      isUser: true,
      timestamp: timestamp ?? DateTime.now(),
      state: MessageState.sending,
    );
  }

  /// Create a new AI message
  factory ChatMessageModel.ai({
    required String content,
    String? agentName,
    String? id,
    DateTime? timestamp,
  }) {
    return ChatMessageModel(
      id: id ?? DateTime.now().millisecondsSinceEpoch.toString(),
      content: content,
      isUser: false,
      timestamp: timestamp ?? DateTime.now(),
      state: MessageState.delivered,
      agentName: agentName,
    );
  }

  factory ChatMessageModel.fromJson(Map<String, dynamic> json) {
    return ChatMessageModel(
      id: json['id'] as String? ?? DateTime.now().millisecondsSinceEpoch.toString(),
      content: json['content'] as String,
      isUser: json['is_user'] as bool? ?? false,
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'] as String)
          : DateTime.now(),
      state: _parseMessageState(json['state'] as String?),
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

  ChatMessageModel copyWith({
    String? id,
    String? content,
    bool? isUser,
    DateTime? timestamp,
    MessageState? state,
    String? agentName,
  }) {
    return ChatMessageModel(
      id: id ?? this.id,
      content: content ?? this.content,
      isUser: isUser ?? this.isUser,
      timestamp: timestamp ?? this.timestamp,
      state: state ?? this.state,
      agentName: agentName ?? this.agentName,
    );
  }

  static MessageState _parseMessageState(String? state) {
    switch (state) {
      case 'sending':
        return MessageState.sending;
      case 'failed':
        return MessageState.failed;
      case 'delivered':
      default:
        return MessageState.delivered;
    }
  }
}

enum MessageState { sending, delivered, failed }
