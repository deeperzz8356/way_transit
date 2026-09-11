import 'package:flutter/material.dart';

class ChatInput extends StatefulWidget {
  final TextEditingController controller;
  final ValueChanged<String> onSubmitted;
  final bool isLoading;
  final VoidCallback? onAttachmentPressed;

  const ChatInput({
    required this.controller,
    required this.onSubmitted,
    this.isLoading = false,
    this.onAttachmentPressed,
    super.key,
  });

  @override
  State<ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends State<ChatInput> {
  late FocusNode _focusNode;
  bool _hasText = false;

  @override
  void initState() {
    super.initState();
    _focusNode = FocusNode();
    widget.controller.addListener(_updateTextState);
  }

  @override
  void didUpdateWidget(ChatInput oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Rebuild UI when isLoading changes
    if (oldWidget.isLoading != widget.isLoading) {
      if (mounted) {
        setState(() {});
      }
    }
  }

  @override
  void dispose() {
    _focusNode.dispose();
    widget.controller.removeListener(_updateTextState);
    super.dispose();
  }

  void _updateTextState() {
    setState(() => _hasText = widget.controller.text.trim().isNotEmpty);
  }

  void _sendMessage() {
    final text = widget.controller.text.trim();
    if (text.isNotEmpty && !widget.isLoading) {
      widget.onSubmitted(text);
      widget.controller.clear();
      // Ensure UI updates when text is cleared
      setState(() => _hasText = false);
      _focusNode.requestFocus();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 12,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFFF0F2F7),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: _focusNode.hasFocus ? const Color(0xFF5974FF) : Colors.transparent,
                width: 1.5,
              ),
            ),
            child: Row(
              children: [
                const SizedBox(width: 16),
                if (widget.isLoading)
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: Center(
                      child: SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.grey[500]!),
                        ),
                      ),
                    ),
                  )
                else
                  GestureDetector(
                    onTap: widget.onAttachmentPressed,
                    child: const Icon(Icons.add, color: Color(0xFF8C90A3), size: 24),
                  ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: widget.controller,
                    focusNode: _focusNode,
                    maxLines: null,
                    minLines: 1,
                    enabled: !widget.isLoading,
                    decoration: InputDecoration(
                      hintText: 'Ask WAY AI anything about your journey...',
                      hintStyle: TextStyle(color: Colors.grey[400], fontSize: 14),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 0, vertical: 8),
                    ),
                    style: const TextStyle(fontSize: 14, color: Color(0xFF1A1B35)),
                    onSubmitted: (_) {
                      if (!widget.isLoading) {
                        _sendMessage();
                      }
                    },
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: _hasText && !widget.isLoading ? _sendMessage : null,
                  child: Container(
                    margin: const EdgeInsets.only(right: 4),
                    child: Icon(
                      Icons.send_rounded,
                      color: _hasText && !widget.isLoading
                          ? const Color(0xFF5974FF)
                          : Colors.grey[300],
                      size: 24,
                    ),
                  ),
                ),
                const SizedBox(width: 4),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
