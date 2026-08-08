import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../models/booking.dart';
import '../services/api_service.dart';
import 'add_ticket_screen.dart';
import 'ticket_detail_screen.dart';

class TripDetailScreen extends StatefulWidget {
  final TicketTrip trip;

  const TripDetailScreen({super.key, required this.trip});

  @override
  State<TripDetailScreen> createState() => _TripDetailScreenState();
}

class _TripDetailScreenState extends State<TripDetailScreen> {
  final _api = ApiService();
  late TicketTrip _trip;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _trip = widget.trip;
    _refresh();
  }

  Color _colorFor(String? hex, String? mode) {
    final raw = (hex != null && hex.isNotEmpty)
        ? hex
        : PlatformColors.forMode(mode);
    final cleaned = raw.replaceFirst('#', '');
    return Color(int.parse('FF$cleaned', radix: 16));
  }

  Future<void> _ensureToken() async {
    final prefs = await SharedPreferences.getInstance();
    _api.setToken(prefs.getString('token') ?? 'dev-token');
  }

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await _ensureToken();
      final trip = await _api.getTrip(_trip.id);
      if (!mounted) return;
      setState(() {
        _trip = trip;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
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

  Future<void> _rename() async {
    final ctrl = TextEditingController(text: _trip.name);
    final name = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Rename trip'),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Trip name',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, ctrl.text.trim()),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    if (name == null || name.isEmpty || name == _trip.name) return;
    try {
      await _ensureToken();
      final updated = await _api.updateTrip(_trip.id, name: name);
      if (!mounted) return;
      setState(() => _trip = updated);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _deleteTrip() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete trip?'),
        content: const Text(
          'Tickets stay in your wallet — they will just become ungrouped.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete trip'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await _ensureToken();
      await _api.deleteTrip(_trip.id);
      if (!mounted) return;
      Navigator.pop(context, true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _removeTicket(Booking ticket) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Remove from trip?'),
        content: Text(
          'Move ${_routeLabel(ticket)} back to Other tickets?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Remove'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await _ensureToken();
      final updated = await _api.removeTicketFromTrip(_trip.id, ticket.id);
      if (!mounted) return;
      setState(() => _trip = updated);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _addTickets() async {
    try {
      await _ensureToken();
      final wallet = await _api.getWallet();
      if (!mounted) return;
      final ungrouped = wallet.tickets;

      // Always offer: add existing ungrouped tickets AND/OR add a brand-new ticket.
      final choice = await showModalBottomSheet<String>(
        context: context,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
        ),
        builder: (ctx) => SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const ListTile(
                title: Text(
                  'Add to this trip',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
              ListTile(
                leading: const Icon(Icons.confirmation_number_outlined),
                title: const Text('Add new ticket'),
                subtitle: const Text('Scan or enter a ticket into this trip'),
                onTap: () => Navigator.pop(ctx, 'new'),
              ),
              ListTile(
                leading: const Icon(Icons.playlist_add_check),
                title: const Text('Add existing tickets'),
                subtitle: Text(
                  ungrouped.isEmpty
                      ? 'No ungrouped tickets in wallet'
                      : '${ungrouped.length} ungrouped ticket${ungrouped.length == 1 ? '' : 's'}',
                ),
                enabled: ungrouped.isNotEmpty,
                onTap: ungrouped.isEmpty
                    ? null
                    : () => Navigator.pop(ctx, 'existing'),
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      );

      if (choice == 'new') {
        await _addNewTicket();
        return;
      }
      if (choice != 'existing') return;

      final selected = <int>{};
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
          builder: (ctx, setLocal) => AlertDialog(
            title: const Text('Add existing tickets'),
            content: SizedBox(
              width: double.maxFinite,
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: ungrouped.length,
                itemBuilder: (_, i) {
                  final t = ungrouped[i];
                  final checked = selected.contains(t.id);
                  return CheckboxListTile(
                    value: checked,
                    title: Text(_routeLabel(t)),
                    subtitle: Text(
                      (t.modeLabel ?? t.mode ?? 'other').toUpperCase(),
                    ),
                    onChanged: (v) {
                      setLocal(() {
                        if (v == true) {
                          selected.add(t.id);
                        } else {
                          selected.remove(t.id);
                        }
                      });
                    },
                  );
                },
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('Cancel'),
              ),
              TextButton(
                onPressed: selected.isEmpty
                    ? null
                    : () => Navigator.pop(ctx, true),
                child: Text('Add (${selected.length})'),
              ),
            ],
          ),
        ),
      );
      if (confirmed != true || selected.isEmpty) return;
      final updated =
          await _api.addTicketsToTrip(_trip.id, selected.toList());
      if (!mounted) return;
      setState(() => _trip = updated);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _addNewTicket() async {
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => AddTicketScreen(
          initialTripId: _trip.id,
          initialTripName: _trip.name,
        ),
      ),
    );
    if (saved == true || saved == null) {
      await _refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_trip.name),
        actions: [
          IconButton(
            tooltip: 'Rename',
            onPressed: _rename,
            icon: const Icon(Icons.edit_outlined),
          ),
          IconButton(
            tooltip: 'Delete trip',
            onPressed: _deleteTrip,
            icon: const Icon(Icons.delete_outline),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addTickets,
        icon: const Icon(Icons.add),
        label: const Text('Add tickets'),
      ),
      body: _loading && _trip.tickets.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(_error!, style: const TextStyle(color: Colors.red)),
                    ),
                  Text(
                    '${_trip.ticketCount} ticket${_trip.ticketCount == 1 ? '' : 's'}'
                    '${_trip.travelDate != null ? ' · ${_trip.travelDate}' : ''}',
                    style: TextStyle(color: Colors.grey.shade700),
                  ),
                  if (_trip.notes != null && _trip.notes!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(_trip.notes!),
                  ],
                  const SizedBox(height: 16),
                  if (_trip.tickets.isEmpty)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 32),
                      child: Column(
                        children: [
                          const Text(
                            'No tickets in this trip yet.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.grey, fontSize: 16),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Add a new ticket or move existing ones from your wallet.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.grey),
                          ),
                          const SizedBox(height: 20),
                          ElevatedButton.icon(
                            onPressed: _addNewTicket,
                            icon: const Icon(Icons.confirmation_number_outlined),
                            label: const Text('Add new ticket'),
                          ),
                          TextButton(
                            onPressed: _addTickets,
                            child: const Text('Choose how to add'),
                          ),
                        ],
                      ),
                    )
                  else
                    ..._trip.tickets.map(_buildTicketCard),
                  const SizedBox(height: 72),
                ],
              ),
            ),
    );
  }

  Widget _buildTicketCard(Booking ticket) {
    final color = _colorFor(ticket.colorHex, ticket.mode);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () async {
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => TicketDetailScreen(ticket: ticket),
            ),
          );
          _refresh();
        },
        child: Container(
          decoration: BoxDecoration(
            border: Border(left: BorderSide(color: color, width: 6)),
            borderRadius: BorderRadius.circular(4),
          ),
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      (ticket.modeLabel ?? ticket.mode ?? 'Other').toUpperCase(),
                      style: TextStyle(
                        color: color,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _routeLabel(ticket),
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text('Status: ${ticket.status}'),
                  ],
                ),
              ),
              QrImageView(
                data: ticket.displayQr,
                version: QrVersions.auto,
                size: 56,
              ),
              IconButton(
                tooltip: 'Remove from trip',
                onPressed: () => _removeTicket(ticket),
                icon: const Icon(Icons.link_off),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
