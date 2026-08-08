import 'package:flutter/material.dart';

class AIHelperScreen extends StatefulWidget {
  const AIHelperScreen({super.key});

  @override
  State<AIHelperScreen> createState() => _AIHelperScreenState();
}

class _AIHelperScreenState extends State<AIHelperScreen> {
  final TextEditingController _textController = TextEditingController();

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  void _submitQuery(String query) {
    debugPrint('Submitting query: $query');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FE),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              _buildHeader(),
              const SizedBox(height: 32),
              _buildAIBubbles(),
              const SizedBox(height: 32),
              _buildAskAIBar(),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'How can we\nhelp you?',
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1A1B35),
              height: 1.2,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "50°C | 19'Mar'26 | 11:36",
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAIBubbles() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Column(
        children: [
          _buildAIBubble(
            'Plan a new\nJourney 💼 ↗',
            const Color(0xFFEBF0FF),
            () => _submitQuery('Plan a new journey'),
          ),
          const SizedBox(height: 16),
          _buildAIBubble(
            'Plan Weekend\nTrek 💼 ↗',
            const Color(0xFFF4F6FB),
            () => _submitQuery('Plan weekend trek'),
          ),
          const SizedBox(height: 16),
          _buildAIBubble(
            'Start a Group\nChat 💬 ↗',
            const Color(0xFFEBF0FF),
            () => _submitQuery('Start a group chat'),
          ),
        ],
      ),
    );
  }

  Widget _buildAIBubble(String text, Color bgColor, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Text(
          text,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1A1B35),
            height: 1.3,
          ),
        ),
      ),
    );
  }

  Widget _buildAskAIBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.1),
              blurRadius: 10,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            const Text('✨', style: TextStyle(fontSize: 20)),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                controller: _textController,
                decoration: const InputDecoration(
                  hintText: 'Ask AI',
                  hintStyle: TextStyle(
                    color: Color(0xFF8C90A3),
                  ),
                  border: InputBorder.none,
                ),
                onSubmitted: (value) {
                  if (value.trim().isNotEmpty) {
                    _submitQuery(value);
                    _textController.clear();
                  }
                },
              ),
            ),
            const SizedBox(width: 12),
            GestureDetector(
              onTap: () {
                if (_textController.text.trim().isNotEmpty) {
                  _submitQuery(_textController.text);
                  _textController.clear();
                }
              },
              child: const Text('🎤', style: TextStyle(fontSize: 20)),
            ),
          ],
        ),
      ),
    );
  }
}
