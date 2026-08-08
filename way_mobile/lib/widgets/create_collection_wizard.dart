import 'package:flutter/material.dart';

import '../models/booking.dart';
import '../services/api_service.dart';

/// One-screen wizard: name a collection, optionally pick tickets, create it.
/// Returns the created [TicketTrip], or null if cancelled.
Future<TicketTrip?> showCreateCollectionWizard(
  BuildContext context, {
  required ApiService api,
  List<Booking> selectableTickets = const [],
}) {
  return showModalBottomSheet<TicketTrip>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (ctx) => CreateCollectionWizard(
      api: api,
      selectableTickets: selectableTickets,
    ),
  );
}

class CreateCollectionWizard extends StatefulWidget {
  final ApiService api;
  final List<Booking> selectableTickets;

  const CreateCollectionWizard({
    super.key,
    required this.api,
    this.selectableTickets = const [],
  });

  @override
  State<CreateCollectionWizard> createState() => _CreateCollectionWizardState();
}

class _CreateCollectionWizardState extends State<CreateCollectionWizard> {
  final _nameCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  final Set<int> _selected = {};
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  String _routeLabel(Booking ticket) {
    final source = ticket.source?.trim();
    final destination = ticket.destination?.trim();
    if ((source == null || source.isEmpty) &&
        (destination == null || destination.isEmpty)) {
      return 'Unknown ➔ Unknown';
    }
    return '${source?.isNotEmpty == true ? source : 'Unknown'} ➔ '
        '${destination?.isNotEmpty == true ? destination : 'Unknown'}';
  }

  Future<void> _submit() async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Enter a name for this collection');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final trip = await widget.api.createTrip(
        name: name,
        notes: _notesCtrl.text.trim().isEmpty ? null : _notesCtrl.text.trim(),
      );
      TicketTrip result = trip;
      if (_selected.isNotEmpty) {
        result = await widget.api.addTicketsToTrip(
          trip.id,
          _selected.toList(),
        );
      }
      if (!mounted) return;
      Navigator.pop(context, result);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    final tickets = widget.selectableTickets;
    final maxListHeight = MediaQuery.of(context).size.height * 0.35;

    return Padding(
      padding: EdgeInsets.fromLTRB(20, 12, 20, 16 + bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.shade300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Create collection',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Text(
            'Name it, then optionally pick tickets to put inside.',
            style: TextStyle(color: Colors.grey.shade600),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _nameCtrl,
            autofocus: true,
            enabled: !_saving,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(
              labelText: 'Collection name *',
              hintText: 'e.g. Mumbai weekend',
              border: OutlineInputBorder(),
            ),
            onSubmitted: (_) => _submit(),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _notesCtrl,
            enabled: !_saving,
            maxLines: 2,
            decoration: const InputDecoration(
              labelText: 'Notes (optional)',
              border: OutlineInputBorder(),
            ),
          ),
          if (tickets.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(
              'Add tickets now (${_selected.length} selected)',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            ConstrainedBox(
              constraints: BoxConstraints(maxHeight: maxListHeight),
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: tickets.length,
                itemBuilder: (_, i) {
                  final t = tickets[i];
                  final checked = _selected.contains(t.id);
                  return CheckboxListTile(
                    dense: true,
                    value: checked,
                    title: Text(_routeLabel(t)),
                    subtitle: Text(
                      (t.modeLabel ?? t.mode ?? 'other').toUpperCase(),
                    ),
                    onChanged: _saving
                        ? null
                        : (v) {
                            setState(() {
                              if (v == true) {
                                _selected.add(t.id);
                              } else {
                                _selected.remove(t.id);
                              }
                            });
                          },
                  );
                },
              ),
            ),
          ] else ...[
            const SizedBox(height: 12),
            Text(
              'No ungrouped tickets yet — you can add them after creating.',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _saving ? null : _submit,
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            child: Text(
              _saving
                  ? 'Creating…'
                  : (_selected.isEmpty
                      ? 'Create collection'
                      : 'Create with ${_selected.length} ticket${_selected.length == 1 ? '' : 's'}'),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ),
          TextButton(
            onPressed: _saving ? null : () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );
  }
}
