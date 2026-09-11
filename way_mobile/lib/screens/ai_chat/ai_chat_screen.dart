import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import '../../models/chat_message.dart';
import '../../services/ai_chat_service.dart' hide MessageState;
import 'widgets/chat_bubble.dart';
import 'widgets/chat_input.dart';
import 'widgets/typing_indicator.dart';
import 'widgets/suggestion_card.dart';

class AIChatScreen extends StatefulWidget {
  const AIChatScreen({super.key});

  @override
  State<AIChatScreen> createState() => _AIChatScreenState();
}

class _AIChatScreenState extends State<AIChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  late AIChatService _chatService;

  final List<ChatMessageModel> _messages = [];
  bool _isLoading = false;
  String? _sessionId;
  String? _userId;
  bool _serviceHealthy = false;
  bool _shouldShowEmpty = true;

  final List<Map<String, String>> _suggestions = [
    {'emoji': '🚆', 'title': 'Find the best route', 'description': 'Get optimal transport options'},
    {'emoji': '💰', 'title': 'Find the cheapest option', 'description': 'Budget-friendly journey'},
    {'emoji': '⚡', 'title': 'Find the fastest route', 'description': 'Quickest travel time'},
    {'emoji': '🚌', 'title': 'Compare transport options', 'description': 'See all available modes'},
    {'emoji': '🗺️', 'title': 'Plan my journey', 'description': 'Step-by-step directions'},
    {'emoji': '💡', 'title': 'Travel tips', 'description': 'Helpful travel advice'},
  ];

  @override
  void initState() {
    super.initState();
    _initializeChat();
  }

  Future<void> _initializeChat() async {
    try {
      final firebaseUser = firebase_auth.FirebaseAuth.instance.currentUser;
      if (firebaseUser == null) {
        setState(() {
          _serviceHealthy = false;
        });
        _showError('Please log in to use the chatbot');
        return;
      }

      _userId = firebaseUser.uid;
      _sessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';

      // Initialize AI Chat Service with auth token
      final idToken = await firebaseUser.getIdToken();
      _chatService = AIChatService(authToken: idToken);

      // Check service health
      final isHealthy = await _chatService.checkHealth();
      if (mounted) {
        setState(() => _serviceHealthy = isHealthy);
        if (!isHealthy) {
          _showError('WAY AI is temporarily unavailable. Please try again later.');
        }
      }
    } catch (e) {
      if (mounted) {
        _showError('Failed to initialize chat: ${e.toString()}');
      }
    }
  }

  Future<void> _sendMessage(String content) async {
    if (content.trim().isEmpty || _isLoading || !_serviceHealthy) {
      return;
    }

    // Create user message
    final userMessage = ChatMessageModel.user(content: content);

    setState(() {
      _messages.add(userMessage);
      _isLoading = true;
      _shouldShowEmpty = false;
    });

    _scrollToBottom();

    try {
      // Send to AI service
      final response = await _chatService.sendMessage(
        message: content,
        userId: _userId,
        sessionId: _sessionId,
      );

      // Create AI response message
      final aiMessage = ChatMessageModel.ai(content: response.response, agentName: response.agent);

      if (mounted) {
        setState(() {
          _messages.add(aiMessage);
          _isLoading = false;
        });
        _scrollToBottom();
      }
    } on AIChatException catch (e) {
      if (mounted) {
        _showError(e.message);
        setState(() {
          _isLoading = false;
          // Add failed message
          _messages.add(
            ChatMessageModel.ai(
              content: e.message,
              agentName: 'Error',
            ).copyWith(state: MessageState.failed),
          );
        });
      }
    } catch (e) {
      if (mounted) {
        _showError('An unexpected error occurred: ${e.toString()}');
        setState(() => _isLoading = false);
      }
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red[700],
        duration: const Duration(seconds: 4),
        action: SnackBarAction(label: 'Dismiss', textColor: Colors.white, onPressed: () {}),
      ),
    );
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 300), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _clearChat() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear conversation?'),
        content: const Text(
          'This will clear your current chat history. This action cannot be undone.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              setState(() {
                _messages.clear();
                _shouldShowEmpty = true;
                _sessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';
              });
            },
            child: const Text('Clear', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FE),
      appBar: _buildAppBar(),
      body: _buildBody(),
      bottomSheet: _buildBottomSheet(),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 1,
      centerTitle: false,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_ios_new),
        onPressed: () => Navigator.pop(context),
      ),
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'WAY AI',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35)),
          ),
          Text(
            _serviceHealthy ? 'Online • Your intelligent travel assistant' : 'Offline',
            style: TextStyle(
              fontSize: 11,
              color: _serviceHealthy ? Colors.grey[600] : Colors.red[600],
              fontWeight: FontWeight.w400,
            ),
          ),
        ],
      ),
      actions: [
        if (_messages.isNotEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8.0),
            child: PopupMenuButton(
              icon: const Icon(Icons.more_vert),
              itemBuilder: (context) => [
                PopupMenuItem(child: const Text('Clear conversation'), onTap: _clearChat),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildBody() {
    if (!_serviceHealthy) {
      return _buildServiceUnavailable();
    }

    if (_shouldShowEmpty && _messages.isEmpty) {
      return _buildEmptyState();
    }

    return Stack(
      children: [
        ListView.builder(
          controller: _scrollController,
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(vertical: 16),
          itemCount: _messages.length + (_isLoading ? 1 : 0),
          itemBuilder: (context, index) {
            if (index == _messages.length) {
              return const TypingIndicator();
            }

            final message = _messages[index];
            return ChatBubble(
              message: message,
              onRetry: message.state == MessageState.failed
                  ? () => _sendMessage(message.content)
                  : null,
            );
          },
        ),
      ],
    );
  }

  Widget _buildEmptyState() {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const SizedBox(height: 32),
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: const Color(0xFFEBF0FF),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Center(child: Text('🤖', style: TextStyle(fontSize: 40))),
            ),
            const SizedBox(height: 24),
            const Text(
              'Hi! I\'m WAY AI 👋',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35)),
            ),
            const SizedBox(height: 8),
            Text(
              'Your intelligent travel assistant for smarter journeys.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: Colors.grey[600], height: 1.5),
            ),
            const SizedBox(height: 40),
            Text(
              'Try asking me about:',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.grey[700]),
            ),
            const SizedBox(height: 16),
            ..._suggestions.map(
              (suggestion) => SuggestionCard(
                emoji: suggestion['emoji']!,
                title: suggestion['title']!,
                description: suggestion['description'],
                onTap: () => _sendMessage(suggestion['title']!),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildServiceUnavailable() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: Colors.red[50],
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Center(child: Icon(Icons.cloud_off, size: 40, color: Colors.red)),
            ),
            const SizedBox(height: 24),
            const Text(
              'WAY AI Offline',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35)),
            ),
            const SizedBox(height: 12),
            Text(
              'WAY AI is temporarily unavailable. Please check your connection and try again.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: Colors.grey[600], height: 1.5),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _initializeChat,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF5974FF),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomSheet() {
    return ChatInput(
      controller: _messageController,
      onSubmitted: _sendMessage,
      isLoading: _isLoading,
      onAttachmentPressed: null,
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
