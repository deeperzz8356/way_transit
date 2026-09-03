import 'package:flutter/material.dart';
import '../../../models/chat_message.dart';

class ChatBubble extends StatefulWidget {
  final ChatMessageModel message;
  final VoidCallback? onRetry;

  const ChatBubble({required this.message, this.onRetry, super.key});

  @override
  State<ChatBubble> createState() => _ChatBubbleState();
}

class _ChatBubbleState extends State<ChatBubble> {
  bool _showCopyFeedback = false;

  void _copyToClipboard() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Copied to clipboard'), duration: Duration(milliseconds: 1500)),
    );
    setState(() {
      _showCopyFeedback = true;
    });
    Future.delayed(const Duration(seconds: 1), () {
      if (mounted) {
        setState(() => _showCopyFeedback = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 600;

    if (widget.message.isUser) {
      return _buildUserMessage(context, isMobile);
    } else {
      return _buildAIMessage(context, isMobile);
    }
  }

  Widget _buildUserMessage(BuildContext context, bool isMobile) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          Flexible(
            child: Container(
              constraints: BoxConstraints(
                maxWidth: isMobile
                    ? MediaQuery.of(context).size.width * 0.75
                    : MediaQuery.of(context).size.width * 0.6,
              ),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFF5974FF),
                borderRadius: BorderRadius.circular(18),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF5974FF).withValues(alpha: 0.2),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    widget.message.content,
                    style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.4),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _formatTime(widget.message.timestamp),
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 11),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAIMessage(BuildContext context, bool isMobile) {
    final errorState = widget.message.state == MessageState.failed;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildAIAvatar(),
          const SizedBox(width: 12),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  constraints: BoxConstraints(
                    maxWidth: isMobile
                        ? MediaQuery.of(context).size.width * 0.75
                        : MediaQuery.of(context).size.width * 0.6,
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF0F2F7),
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.05),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (widget.message.agentName != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Text(
                            widget.message.agentName!,
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF8C90A3),
                            ),
                          ),
                        ),
                      if (errorState) _buildErrorContent() else _buildAIContent(),
                    ],
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      _formatTime(widget.message.timestamp),
                      style: TextStyle(color: Colors.grey[600], fontSize: 11),
                    ),
                    if (!errorState) ...[
                      const SizedBox(width: 12),
                      GestureDetector(
                        onTap: _copyToClipboard,
                        child: Text(
                          _showCopyFeedback ? '✓ Copied' : 'Copy',
                          style: TextStyle(
                            color: _showCopyFeedback ? const Color(0xFF5974FF) : Colors.grey[600],
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                if (errorState && widget.onRetry != null) ...[
                  const SizedBox(height: 8),
                  GestureDetector(
                    onTap: widget.onRetry,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.transparent,
                        border: Border.all(color: const Color(0xFF5974FF)),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text(
                        'Retry',
                        style: TextStyle(
                          color: Color(0xFF5974FF),
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAIAvatar() {
    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        color: const Color(0xFF5974FF),
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Center(child: Text('🤖', style: TextStyle(fontSize: 18))),
    );
  }

  Widget _buildAIContent() {
    return _MarkdownRenderer(text: widget.message.content);
  }

  Widget _buildErrorContent() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.message.content,
          style: const TextStyle(color: Color(0xFFDC2626), fontSize: 14, height: 1.5),
        ),
      ],
    );
  }

  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final difference = now.difference(time);

    if (difference.inSeconds < 60) {
      return 'now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else {
      return '${time.month}/${time.day} ${time.hour}:${time.minute.toString().padLeft(2, '0')}';
    }
  }
}

/// Simple Markdown renderer for chat messages
class _MarkdownRenderer extends StatelessWidget {
  final String text;

  const _MarkdownRenderer({required this.text});

  @override
  Widget build(BuildContext context) {
    return SelectableText.rich(
      _parseMarkdown(text),
      style: const TextStyle(color: Color(0xFF1A1B35), fontSize: 14, height: 1.5),
    );
  }

  TextSpan _parseMarkdown(String text) {
    final children = <InlineSpan>[];

    // Pattern matching for markdown elements
    final patterns = <(RegExp pattern, TextSpan Function(RegExpMatch match) builder)>[
      // Bold: **text**
      (
        RegExp(r'\*\*(.*?)\*\*'),
        (match) => TextSpan(
          text: match.group(1),
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      // Italic: *text* (but not **text**)
      (
        RegExp(r'(?<!\*)\*(.*?)\*(?!\*)'),
        (match) => TextSpan(
          text: match.group(1),
          style: const TextStyle(fontStyle: FontStyle.italic),
        ),
      ),
      // Code: `text`
      (
        RegExp(r'`([^`]+)`'),
        (match) => TextSpan(
          text: match.group(1),
          style: TextStyle(
            fontFamily: 'monospace',
            backgroundColor: Colors.grey[200],
            color: const Color(0xFF5974FF),
          ),
        ),
      ),
    ];

    // Sort matches by position
    final allMatches = <(int start, int end, InlineSpan span)>[];

    for (final (pattern, builder) in patterns) {
      for (final match in pattern.allMatches(text)) {
        allMatches.add((match.start, match.end, builder(match)));
      }
    }

    allMatches.sort((a, b) => a.$1.compareTo(b.$1));

    // Build the final text spans avoiding overlaps
    var currentPos = 0;
    for (final (start, end, span) in allMatches) {
      if (start >= currentPos) {
        if (start > currentPos) {
          children.add(TextSpan(text: text.substring(currentPos, start)));
        }
        children.add(span);
        currentPos = end;
      }
    }

    if (currentPos < text.length) {
      children.add(TextSpan(text: text.substring(currentPos)));
    }

    return TextSpan(children: children.isEmpty ? [TextSpan(text: text)] : children);
  }
}
