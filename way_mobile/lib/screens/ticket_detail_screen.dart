import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../models/booking.dart';
import '../services/api_service.dart';
import '../nav/app_nav.dart';
import '../widgets/trip_picker_sheet.dart';

class TicketDetailScreen extends StatefulWidget {
  final Booking ticket;

  const TicketDetailScreen({super.key, required this.ticket});

  @override
  State<TicketDetailScreen> createState() => _TicketDetailScreenState();
}

class _TicketDetailScreenState extends State<TicketDetailScreen> {
  late Booking _ticket;
  final _api = ApiService();
  bool _busy = false;
  String? _tripName;

  @override
  void initState() {
    super.initState();
    _ticket = widget.ticket;
    _loadTripName();
  }

  Color get _color {
    final raw = (_ticket.colorHex?.isNotEmpty == true)
        ? _ticket.colorHex!
        : PlatformColors.forMode(_ticket.mode);
    return Color(int.parse('FF${raw.replaceFirst('#', '')}', radix: 16));
  }

  Future<void> _ensureAuth() async {
    final prefs = await SharedPreferences.getInstance();
    _api.setToken(prefs.getString('token') ?? 'dev-token');
  }

  Future<void> _loadTripName() async {
    final tripId = _ticket.ticketTripId;
    if (tripId == null) {
      setState(() => _tripName = null);
      return;
    }
    try {
      await _ensureAuth();
      final trip = await _api.getTrip(tripId);
      if (!mounted) return;
      setState(() => _tripName = trip.name);
    } catch (_) {
      if (!mounted) return;
      setState(() => _tripName = 'Trip #$tripId');
    }
  }

  Future<void> _moveToTrip() async {
    setState(() => _busy = true);
    try {
      await _ensureAuth();
      final trips = await _api.listTrips();
      if (!mounted) return;
      final result = await showTripPickerSheet(context, trips: trips);
      if (result == null) {
        setState(() => _busy = false);
        return;
      }
      int tripId;
      String? name;
      if (result.isCreate) {
        final trip = await _api.createTrip(
          name: result.newName!,
          notes: result.newNotes,
          travelDate: result.newTravelDate,
        );
        tripId = trip.id;
        name = trip.name;
      } else {
        tripId = result.tripId!;
        final matches = trips.where((t) => t.id == tripId);
        name = matches.isEmpty ? null : matches.first.name;
      }
      await _api.addTicketsToTrip(tripId, [_ticket.id]);
      if (!mounted) return;
      setState(() {
        _ticket = _ticket.copyWith(ticketTripId: tripId);
        _tripName = name ?? 'Trip';
        _busy = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Moved to ${_tripName ?? 'trip'}')),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _removeFromTrip() async {
    final tripId = _ticket.ticketTripId;
    if (tripId == null) return;
    setState(() => _busy = true);
    try {
      await _ensureAuth();
      await _api.removeTicketFromTrip(tripId, _ticket.id);
      if (!mounted) return;
      setState(() {
        _ticket = _ticket.copyWith(clearTrip: true);
        _tripName = null;
        _busy = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Removed from trip')),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  String _fmt(DateTime? dt) {
    if (dt == null) return '—';
    final local = dt.toLocal();
    final h = local.hour.toString().padLeft(2, '0');
    final m = local.minute.toString().padLeft(2, '0');
    return '${local.year}-${local.month.toString().padLeft(2, '0')}-${local.day.toString().padLeft(2, '0')} $h:$m';
  }

  Future<DateTime?> _pickDateTime({
    required String title,
    required DateTime initial,
  }) async {
    final date = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime.now().subtract(const Duration(days: 1)),
      lastDate: DateTime.now().add(const Duration(days: 30)),
      helpText: title,
    );
    if (date == null || !mounted) return null;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(initial),
      helpText: title,
    );
    if (time == null) return null;
    return DateTime(date.year, date.month, date.day, time.hour, time.minute);
  }

  Future<Map<String, DateTime>?> _askJourneyTimes() async {
    var start = DateTime.now();
    var end = start.add(const Duration(hours: 1));

    return showDialog<Map<String, DateTime>>(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setLocal) {
            return AlertDialog(
              title: const Text('Start journey'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'This ticket becomes your Active journey. '
                    'Any other active journey is switched off.',
                    style: TextStyle(fontSize: 13, color: Colors.black54),
                  ),
                  const SizedBox(height: 16),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Start time'),
                    subtitle: Text(_fmt(start)),
                    trailing: const Icon(Icons.schedule),
                    onTap: () async {
                      final picked = await _pickDateTime(
                        title: 'Start time',
                        initial: start,
                      );
                      if (picked != null) {
                        setLocal(() {
                          start = picked;
                          if (!end.isAfter(start)) {
                            end = start.add(const Duration(hours: 1));
                          }
                        });
                      }
                    },
                  ),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Estimated end time'),
                    subtitle: Text(_fmt(end)),
                    trailing: const Icon(Icons.flag),
                    onTap: () async {
                      final picked = await _pickDateTime(
                        title: 'Estimated end',
                        initial: end,
                      );
                      if (picked != null) {
                        setLocal(() => end = picked);
                      }
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: () {
                    if (!end.isAfter(start)) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('End time must be after start time'),
                        ),
                      );
                      return;
                    }
                    Navigator.pop(ctx, {'start': start, 'end': end});
                  },
                  child: const Text('Make Active'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _startJourney() async {
    final times = await _askJourneyTimes();
    if (times == null) return;

    setState(() => _busy = true);
    try {
      await _ensureAuth();
      await _api.startJourney(
        _ticket.id,
        startTime: times['start'],
        estimatedEndTime: times['end'],
        makeActive: true,
      );
      if (!mounted) return;
      // Leave ticket detail → switch to Home tab with active journey UI
      Navigator.of(context).pop();
      AppNav.goHomeAndRefresh();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Active journey on Home')),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _deleteTicket() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete ticket?'),
        content: const Text(
          'This removes the ticket from your unified wallet. This cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (ok != true) return;

    setState(() => _busy = true);
    try {
      await _ensureAuth();
      await _api.deleteTicket(_ticket.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ticket deleted')),
      );
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_ticket.modeLabel ?? 'Ticket'),
        backgroundColor: _color,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            onPressed: _busy ? null : _deleteTicket,
            icon: const Icon(Icons.delete_outline),
            tooltip: 'Delete ticket',
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          if (_ticket.activeBadge)
            Center(
              child: Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.green.shade600,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  'ACTIVE JOURNEY',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                    letterSpacing: 0.6,
                  ),
                ),
              ),
            ),
          Center(
            child: QrImageView(
              data: _ticket.displayQr,
              version: QrVersions.auto,
              size: 220,
            ),
          ),
          const SizedBox(height: 8),
          Center(
            child: SelectableText(
              _ticket.displayQr,
              textAlign: TextAlign.center,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            '${_ticket.source ?? 'Unknown'} ➔ ${_ticket.destination ?? 'Unknown'}',
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          _row('Platform', (_ticket.mode ?? 'other').toUpperCase()),
          _row('Status', _ticket.status),
          if (_ticket.ticketNumber != null)
            _row('Ticket No', _ticket.ticketNumber!),
          if (_ticket.operatorName != null)
            _row('Operator', _ticket.operatorName!),
          if (_ticket.className != null) _row('Class', _ticket.className!),
          if (_ticket.fare != null)
            _row('Fare', '₹${_ticket.fare!.toStringAsFixed(0)}'),
          if (_ticket.travelDate != null) _row('Date', _ticket.travelDate!),
          if (_ticket.journeyStartedAt != null)
            _row('Start', _fmt(_ticket.journeyStartedAt)),
          if (_ticket.journeyEstimatedEndAt != null)
            _row('Est. end', _fmt(_ticket.journeyEstimatedEndAt)),
          _row(
            'Trip',
            _ticket.ticketTripId == null
                ? 'Ungrouped'
                : (_tripName ?? 'Trip #${_ticket.ticketTripId}'),
          ),
          if (_ticket.imageUrl != null && _ticket.imageUrl!.isNotEmpty) ...[
            const SizedBox(height: 16),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.network(
                ApiConfig.resolveUrl(_ticket.imageUrl!),
                height: 160,
                fit: BoxFit.cover,
                errorBuilder: (_, error, stackTrace) => const SizedBox.shrink(),
              ),
            ),
          ],
          const SizedBox(height: 24),
          if (_ticket.status.toUpperCase() != 'USED' &&
              _ticket.status.toUpperCase() != 'EXPIRED')
            ElevatedButton.icon(
              onPressed: _busy ? null : _startJourney,
              icon: const Icon(Icons.play_arrow_rounded),
              style: ElevatedButton.styleFrom(
                backgroundColor: _color,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              label: Text(
                _busy
                    ? 'Starting…'
                    : (_ticket.activeBadge
                        ? 'Update Active → Home'
                        : 'Start → Home'),
              ),
            ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _busy ? null : _moveToTrip,
            icon: const Icon(Icons.folder_outlined),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            label: Text(
              _ticket.ticketTripId == null ? 'Add to trip' : 'Move to trip',
            ),
          ),
          if (_ticket.ticketTripId != null) ...[
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _busy ? null : _removeFromTrip,
              icon: const Icon(Icons.link_off),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              label: const Text('Remove from trip'),
            ),
          ],
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: _busy ? null : _deleteTicket,
            icon: const Icon(Icons.delete_forever),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red.shade600,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            label: const Text('Delete ticket'),
          ),
        ],
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(label,
                style: const TextStyle(color: Colors.black54)),
          ),
          Expanded(
            child: Text(value,
                style: const TextStyle(fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}
