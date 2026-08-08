import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';

/// Chat with WAY Ticketing / multi-agent backend at `/agent/chat`.
class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<_Message> _messages = [
    _Message(
      sender: Sender.agent,
      text:
          'Ask about your wallet — e.g. “show my metro tickets” or “start journey on latest rail ticket”.',
      agentName: 'Ticketing Agent',
    ),
  ];
  final TextEditingController _controller = TextEditingController();
  bool _loading = false;

  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token') ?? prefs.getString('auth_token');
  }

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty) return;
    setState(() {
      _messages.add(_Message(sender: Sender.user, text: text));
      _loading = true;
    });
    _controller.clear();

    final token = await _getToken();
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/agent/chat'),
        headers: {
          'Content-Type': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
        body: jsonEncode({'message': text}),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final agentMsg = _Message(
          sender: Sender.agent,
          text: data['response'] ?? '',
          agentName: data['agent'] ?? 'Agent',
        );
        setState(() => _messages.add(agentMsg));
      } else {
        setState(() => _messages.add(_Message(
              sender: Sender.system,
              text: 'Error: ${response.statusCode} ${response.body}',
            )));
      }
    } catch (e) {
      setState(() => _messages.add(_Message(
            sender: Sender.system,
            text: 'Error: Could not reach the WAY Transit Agent ($e).',
          )));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('WAY AI Assistant'),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg.sender == Sender.user;
                final bgColor = isUser
                    ? const Color(0xFF007bff)
                    : (msg.sender == Sender.system
                        ? const Color(0xFFff4d4f)
                        : const Color(0xFFF1F0F0));
                final textColor = isUser || msg.sender == Sender.system
                    ? Colors.white
                    : Colors.black;
                return Align(
                  alignment:
                      isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin:
                        const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: bgColor,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (msg.sender == Sender.agent && msg.agentName != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Text('🤖 ${msg.agentName}',
                                style: const TextStyle(
                                    fontSize: 12, color: Colors.black54)),
                          ),
                        Text(msg.text, style: TextStyle(color: textColor)),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: Text('Agent is typing...',
                  style: TextStyle(fontStyle: FontStyle.italic)),
            ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: 'Type your message...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (value) => _sendMessage(value),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed:
                      _loading ? null : () => _sendMessage(_controller.text),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

enum Sender { user, agent, system }

class _Message {
  final Sender sender;
  final String text;
  final String? agentName;
  _Message({required this.sender, required this.text, this.agentName});
}
