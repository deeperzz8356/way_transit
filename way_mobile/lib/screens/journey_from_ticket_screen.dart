import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../models/booking.dart';
import '../services/api_service.dart';

class JourneyFromTicketScreen extends StatefulWidget {
  final Booking ticket;

  const JourneyFromTicketScreen({super.key, required this.ticket});

  @override
  State<JourneyFromTicketScreen> createState() =>
      _JourneyFromTicketScreenState();
}

class _JourneyFromTicketScreenState extends State<JourneyFromTicketScreen> {
  final _api = ApiService();
  int _step = 0;
  bool _completing = false;

  Color get _color {
    final raw = (widget.ticket.colorHex?.isNotEmpty == true)
        ? widget.ticket.colorHex!
        : PlatformColors.forMode(widget.ticket.mode);
    return Color(int.parse('FF${raw.replaceFirst('#', '')}', radix: 16));
  }

  List<Map<String, dynamic>> get _steps {
    final src = widget.ticket.source ?? 'station';
    final dest = widget.ticket.destination ?? 'station';
    final mode = (widget.ticket.mode ?? 'transit').toUpperCase();
    return [
      {
        'label': 'Walk to $src',
        'icon': Icons.directions_walk,
        'color': Colors.amber,
      },
      {
        'label': 'Take $mode toward $dest',
        'icon': Icons.train,
        'color': _color,
      },
      {
        'label': 'Arrive at $dest',
        'icon': Icons.location_on,
        'color': Colors.blue,
      },
    ];
  }

  Future<void> _complete() async {
    setState(() => _completing = true);
    try {
      final prefs = await SharedPreferences.getInstance();
      _api.setToken(prefs.getString('token') ?? 'dev-token');
      await _api.completeJourney(widget.ticket.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Journey completed — ticket marked USED')),
      );
      Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      setState(() => _completing = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final steps = _steps;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Active Journey'),
        backgroundColor: _color,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              '${widget.ticket.source ?? '?'} → ${widget.ticket.destination ?? '?'}',
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            if (widget.ticket.journeyStartedAt != null ||
                widget.ticket.journeyEstimatedEndAt != null) ...[
              const SizedBox(height: 8),
              Text(
                [
                  if (widget.ticket.journeyStartedAt != null)
                    'Start ${widget.ticket.journeyStartedAt!.toLocal().toString().substring(0, 16)}',
                  if (widget.ticket.journeyEstimatedEndAt != null)
                    'Est. end ${widget.ticket.journeyEstimatedEndAt!.toLocal().toString().substring(0, 16)}',
                ].join('  ·  '),
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.black54, fontSize: 13),
              ),
            ],
            const SizedBox(height: 24),
            ...List.generate(steps.length, (i) {
              final step = steps[i];
              final done = i < _step;
              final current = i == _step;
              return Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: done || current
                          ? step['color'] as Color
                          : Colors.grey.shade300,
                      child: Icon(
                        done ? Icons.check : step['icon'] as IconData,
                        color: Colors.white,
                        size: 18,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        step['label'] as String,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight:
                              current ? FontWeight.bold : FontWeight.normal,
                          color: current ? Colors.black : Colors.black54,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
            const Spacer(),
            if (_step < steps.length - 1)
              ElevatedButton(
                onPressed: () => setState(() => _step++),
                style: ElevatedButton.styleFrom(
                  backgroundColor: _color,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Next step'),
              )
            else
              ElevatedButton(
                onPressed: _completing ? null : _complete,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: Text(
                    _completing ? 'Completing…' : 'Complete journey'),
              ),
          ],
        ),
      ),
    );
  }
}
