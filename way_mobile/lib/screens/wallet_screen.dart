import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../models/booking.dart';
import '../services/api_service.dart';
import '../widgets/create_collection_wizard.dart';
import '../widgets/trip_picker_sheet.dart';
import 'ticket_detail_screen.dart';
import 'trip_detail_screen.dart';

class WalletScreen extends StatefulWidget {
  const WalletScreen({super.key});

  @override
  State<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends State<WalletScreen>
    with SingleTickerProviderStateMixin {
  final _api = ApiService();
  List<TicketTrip> _trips = [];
  List<Booking> _tickets = [];
  List<UserPassItem> _passes = [];
  bool _isLoading = true;
  String? _error;
  String _modeFilter = 'all';
  String _statusTab = 'active'; // active|used|expired|all
  late TabController _statusTabs;

  bool _selectMode = false;
  final Set<int> _selectedIds = {};
  final Set<int> _expandedTripIds = {};

  static const _modes = ['all', 'rail', 'metro', 'bus', 'cab'];

  @override
  void initState() {
    super.initState();
    _statusTabs = TabController(length: 4, vsync: this);
    _statusTabs.addListener(() {
      if (_statusTabs.indexIsChanging) return;
      setState(() {
        _statusTab = ['active', 'used', 'expired', 'all'][_statusTabs.index];
      });
    });
    _loadCachedThenFetch();
  }

  @override
  void dispose() {
    _statusTabs.dispose();
    super.dispose();
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

  Future<void> _loadCachedThenFetch() async {
    final prefs = await SharedPreferences.getInstance();
    final cached = prefs.getString('wallet_cache');
    if (cached != null) {
      try {
        final data = WalletData.fromJson(json.decode(cached));
        if (mounted) {
          setState(() {
            _trips = data.trips;
            _tickets = data.tickets;
            _passes = data.passes;
            _isLoading = false;
          });
        }
      } catch (_) {}
    }
    await _fetchWallet();
  }

  Future<void> _fetchWallet() async {
    setState(() {
      _error = null;
      if (_tickets.isEmpty && _trips.isEmpty) _isLoading = true;
    });

    try {
      await _ensureToken();
      final wallet = await _api.getWallet(
        mode: _modeFilter == 'all' ? null : _modeFilter,
      );
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('wallet_cache', json.encode(wallet.toJson()));

      if (!mounted) return;
      setState(() {
        _trips = wallet.trips;
        _tickets = wallet.tickets;
        _passes = wallet.passes;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  bool _matchesStatus(Booking t) {
    final s = t.status.toUpperCase();
    switch (_statusTab) {
      case 'active':
        return s == 'CONFIRMED' || s == 'IN_PROGRESS';
      case 'used':
        return s == 'USED';
      case 'expired':
        return s == 'EXPIRED';
      default:
        return true;
    }
  }

  List<Booking> _filterTickets(List<Booking> tickets) {
    final list = tickets.where(_matchesStatus).toList();
    list.sort((a, b) {
      if (a.activeBadge != b.activeBadge) {
        return a.activeBadge ? -1 : 1;
      }
      return 0;
    });
    return list;
  }

  List<Booking> get _filteredUngrouped => _filterTickets(_tickets);

  List<TicketTrip> get _visibleTrips {
    // Empty trips always stay visible so "create trip first" works.
    return _trips.where((trip) {
      if (trip.tickets.isEmpty) return true;
      return _filterTickets(trip.tickets).isNotEmpty;
    }).toList();
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

  Future<void> _addDemoPass() async {
    try {
      await _ensureToken();
      final products = await _api.listPassProducts();
      if (products.isEmpty) return;
      await _api.addPassToWallet(products.first.passId);
      await _fetchWallet();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pass added to wallet')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not add pass: $e')),
      );
    }
  }

  void _exitSelectMode() {
    setState(() {
      _selectMode = false;
      _selectedIds.clear();
    });
  }

  Future<void> _createTrip() async {
    await _ensureToken();
    final created = await showCreateCollectionWizard(
      context,
      api: _api,
      selectableTickets: _tickets,
    );
    if (created == null) return;
    await _fetchWallet();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Collection "${created.name}" created')),
    );
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => TripDetailScreen(trip: created),
      ),
    );
    _fetchWallet();
  }

  Future<void> _addSelectedToTrip() async {
    if (_selectedIds.isEmpty) return;
    final result = await showTripPickerSheet(context, trips: _trips);
    if (result == null) return;
    try {
      await _ensureToken();
      int tripId;
      if (result.isCreate) {
        final trip = await _api.createTrip(
          name: result.newName!,
          notes: result.newNotes,
          travelDate: result.newTravelDate,
        );
        tripId = trip.id;
      } else {
        tripId = result.tripId!;
      }
      await _api.addTicketsToTrip(tripId, _selectedIds.toList());
      _exitSelectMode();
      await _fetchWallet();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Tickets added to trip')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final hasContent =
        _passes.isNotEmpty || _visibleTrips.isNotEmpty || _filteredUngrouped.isNotEmpty;

    return Scaffold(
      appBar: AppBar(
        title: Text(_selectMode
            ? '${_selectedIds.length} selected'
            : 'My Unified Wallet'),
        leading: _selectMode
            ? IconButton(
                icon: const Icon(Icons.close),
                onPressed: _exitSelectMode,
              )
            : null,
        actions: [
          if (_selectMode)
            TextButton(
              onPressed: _selectedIds.isEmpty ? null : _addSelectedToTrip,
              child: const Text('Add to collection'),
            )
          else ...[
            IconButton(
              onPressed: () => setState(() => _selectMode = true),
              tooltip: 'Select tickets',
              icon: const Icon(Icons.checklist),
            ),
            IconButton(
              onPressed: _addDemoPass,
              tooltip: 'Add pass',
              icon: const Icon(Icons.card_membership),
            ),
            IconButton(
              onPressed: _fetchWallet,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ],
        bottom: TabBar(
          controller: _statusTabs,
          tabs: const [
            Tab(text: 'Active'),
            Tab(text: 'Used'),
            Tab(text: 'Expired'),
            Tab(text: 'All'),
          ],
        ),
      ),
      floatingActionButton: _selectMode
          ? null
          : FloatingActionButton.extended(
              onPressed: _createTrip,
              icon: const Icon(Icons.create_new_folder_outlined),
              label: const Text('New collection'),
            ),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
            child: Row(
              children: _modes.map((m) {
                final selected = _modeFilter == m;
                final color = _colorFor(null, m == 'all' ? 'other' : m);
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    selected: selected,
                    label: Text(m.toUpperCase()),
                    selectedColor: color.withOpacity(0.25),
                    checkmarkColor: color,
                    onSelected: (_) {
                      setState(() => _modeFilter = m);
                      _fetchWallet();
                    },
                  ),
                );
              }).toList(),
            ),
          ),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null && !hasContent
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text('Error: $_error',
                                  textAlign: TextAlign.center),
                              const SizedBox(height: 12),
                              ElevatedButton(
                                onPressed: _fetchWallet,
                                child: const Text('Retry'),
                              ),
                            ],
                          ),
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _fetchWallet,
                        child: ListView(
                          padding: const EdgeInsets.all(16),
                          children: [
                            if (_passes.isNotEmpty) ...[
                              const Text(
                                'Passes',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 8),
                              ..._passes.map(_buildPassCard),
                              const SizedBox(height: 16),
                            ],
                            if (_visibleTrips.isNotEmpty) ...[
                              const Text(
                                'Collections',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 8),
                              ..._visibleTrips.map(_buildTripSection),
                              const SizedBox(height: 16),
                            ] else if (!_selectMode) ...[
                              Card(
                                color: Colors.blue.shade50,
                                margin: const EdgeInsets.only(bottom: 16),
                                child: Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.stretch,
                                    children: [
                                      const Text(
                                        'Group tickets into a collection',
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 16,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        'Example: “Mumbai weekend” with train + metro + cab tickets.',
                                        style: TextStyle(
                                          color: Colors.grey.shade700,
                                        ),
                                      ),
                                      const SizedBox(height: 12),
                                      ElevatedButton.icon(
                                        onPressed: _createTrip,
                                        icon: const Icon(Icons.add),
                                        label: const Text('Create collection'),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                            if (_filteredUngrouped.isNotEmpty ||
                                (_visibleTrips.isEmpty &&
                                    _passes.isEmpty &&
                                    _filteredUngrouped.isEmpty)) ...[
                              if (_visibleTrips.isNotEmpty ||
                                  _passes.isNotEmpty ||
                                  _trips.isNotEmpty)
                                const Padding(
                                  padding: EdgeInsets.only(bottom: 8),
                                  child: Text(
                                    'Other tickets',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              if (_filteredUngrouped.isEmpty)
                                const Padding(
                                  padding: EdgeInsets.symmetric(vertical: 48),
                                  child: Center(
                                    child: Text(
                                      'No tickets in this view.\nCreate a collection or add a ticket!',
                                      textAlign: TextAlign.center,
                                      style: TextStyle(
                                        fontSize: 16,
                                        color: Colors.grey,
                                      ),
                                    ),
                                  ),
                                )
                              else
                                ..._filteredUngrouped.map(_buildTicketCard),
                            ],
                            const SizedBox(height: 88),
                          ],
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildPassCard(UserPassItem pass) {
    final color = _colorFor(pass.colorHex, pass.modeCoverage);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Container(
        decoration: BoxDecoration(
          border: Border(left: BorderSide(color: color, width: 6)),
          borderRadius: BorderRadius.circular(4),
        ),
        child: ListTile(
          title: Text(pass.name ?? 'Pass',
              style: const TextStyle(fontWeight: FontWeight.bold)),
          subtitle: Text(
            '${(pass.modeCoverage ?? 'other').toUpperCase()} · ${pass.status}'
            '${pass.validUntil != null ? ' · until ${pass.validUntil!.toLocal().toString().split(' ').first}' : ''}',
          ),
          trailing: pass.price != null
              ? Text('₹${pass.price!.toStringAsFixed(0)}')
              : null,
        ),
      ),
    );
  }

  Widget _buildTripSection(TicketTrip trip) {
    final filtered = _filterTickets(trip.tickets);
    final expanded = _expandedTripIds.contains(trip.id) || trip.tickets.isEmpty;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        children: [
          ListTile(
            leading: Icon(
              trip.tickets.isEmpty
                  ? Icons.folder_open_outlined
                  : Icons.folder_special_outlined,
            ),
            title: Text(
              trip.name,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              trip.tickets.isEmpty
                  ? 'Empty · tap to add tickets'
                  : '${filtered.length} ticket${filtered.length == 1 ? '' : 's'}'
                      '${trip.travelDate != null ? ' · ${trip.travelDate}' : ''}',
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: () async {
              if (_selectMode) {
                setState(() {
                  if (_expandedTripIds.contains(trip.id)) {
                    _expandedTripIds.remove(trip.id);
                  } else {
                    _expandedTripIds.add(trip.id);
                  }
                });
                return;
              }
              await Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => TripDetailScreen(trip: trip),
                ),
              );
              _fetchWallet();
            },
          ),
          if (expanded && filtered.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
              child: Column(
                children: filtered
                    .map((t) => _buildTicketCard(t, compact: true))
                    .toList(),
              ),
            ),
          if (expanded && trip.tickets.isEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: OutlinedButton.icon(
                onPressed: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => TripDetailScreen(trip: trip),
                    ),
                  );
                  _fetchWallet();
                },
                icon: const Icon(Icons.add),
                label: const Text('Open & add tickets'),
              ),
            )
          else if (expanded && filtered.isEmpty)
            const Padding(
              padding: EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Text(
                'No tickets match this filter',
                style: TextStyle(color: Colors.grey),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildTicketCard(Booking ticket, {bool compact = false}) {
    final color = _colorFor(ticket.colorHex, ticket.mode);
    final selected = _selectedIds.contains(ticket.id);

    Widget cardBody = Card(
      margin: EdgeInsets.only(bottom: compact ? 8 : 16),
      elevation: ticket.activeBadge ? 6 : 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: selected ? Colors.blue.shade50 : null,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onLongPress: () {
          setState(() {
            _selectMode = true;
            _selectedIds.add(ticket.id);
          });
        },
        onTap: () async {
          if (_selectMode) {
            setState(() {
              if (selected) {
                _selectedIds.remove(ticket.id);
              } else {
                _selectedIds.add(ticket.id);
              }
            });
            return;
          }
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => TicketDetailScreen(ticket: ticket),
            ),
          );
          _fetchWallet();
        },
        child: Container(
          decoration: BoxDecoration(
            border: Border(
              left: BorderSide(
                color: ticket.activeBadge ? Colors.green.shade600 : color,
                width: 6,
              ),
            ),
            borderRadius: BorderRadius.circular(12),
          ),
          padding: EdgeInsets.all(compact ? 12 : 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  if (_selectMode)
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: Icon(
                        selected
                            ? Icons.check_circle
                            : Icons.radio_button_unchecked,
                        color: selected ? Colors.blue : Colors.grey,
                      ),
                    ),
                  Expanded(
                    child: Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: color.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            (ticket.modeLabel ?? ticket.mode ?? 'Other')
                                .toUpperCase(),
                            style: TextStyle(
                              color: color,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        if (ticket.activeBadge)
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: Colors.green.shade600,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: const Text(
                              'ACTIVE',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  if (!_selectMode)
                    IconButton(
                      tooltip: 'Delete ticket',
                      onPressed: () => _confirmDelete(ticket),
                      icon:
                          const Icon(Icons.delete_forever, color: Colors.red),
                    ),
                ],
              ),
              SizedBox(height: compact ? 4 : 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _routeLabel(ticket),
                          style: TextStyle(
                            fontSize: compact ? 15 : 17,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          ticket.activeBadge
                              ? 'Status: ACTIVE JOURNEY'
                              : 'Status: ${ticket.status}',
                          style: TextStyle(
                            color: ticket.activeBadge
                                ? Colors.green.shade700
                                : ticket.status == 'USED'
                                    ? Colors.grey
                                    : Colors.green,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        if (!compact && ticket.ticketNumber != null &&
                            ticket.ticketNumber!.isNotEmpty)
                          Text('No: ${ticket.ticketNumber}',
                              style: const TextStyle(color: Colors.black54)),
                      ],
                    ),
                  ),
                  if (!compact)
                    Column(
                      children: [
                        QrImageView(
                          data: ticket.displayQr,
                          version: QrVersions.auto,
                          size: 80,
                        ),
                        Text(
                          ticket.displayQr.length > 8
                              ? ticket.displayQr.substring(0, 8).toUpperCase()
                              : ticket.displayQr.toUpperCase(),
                          style: const TextStyle(
                            fontSize: 11,
                            fontFamily: 'monospace',
                            color: Colors.grey,
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );

    if (_selectMode || compact) return cardBody;

    return Dismissible(
      key: ValueKey('ticket-${ticket.id}'),
      direction: DismissDirection.endToStart,
      confirmDismiss: (_) async {
        return await showDialog<bool>(
              context: context,
              builder: (ctx) => AlertDialog(
                title: const Text('Delete ticket?'),
                content: Text(
                  'Remove ${_routeLabel(ticket)} from your wallet?',
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
            ) ??
            false;
      },
      onDismissed: (_) async {
        try {
          await _ensureToken();
          await _api.deleteTicket(ticket.id);
          if (!mounted) return;
          setState(() {
            _tickets.removeWhere((t) => t.id == ticket.id);
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Ticket deleted')),
          );
        } catch (e) {
          if (!mounted) return;
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text('$e')));
          _fetchWallet();
        }
      },
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          color: Colors.red.shade400,
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Icon(Icons.delete, color: Colors.white),
      ),
      child: cardBody,
    );
  }

  Future<void> _confirmDelete(Booking ticket) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete ticket?'),
        content: Text('Remove ${_routeLabel(ticket)} from your wallet?'),
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
    try {
      await _ensureToken();
      await _api.deleteTicket(ticket.id);
      if (!mounted) return;
      setState(() {
        _tickets.removeWhere((t) => t.id == ticket.id);
        for (var i = 0; i < _trips.length; i++) {
          final trip = _trips[i];
          if (trip.tickets.any((t) => t.id == ticket.id)) {
            final remaining =
                trip.tickets.where((t) => t.id != ticket.id).toList();
            _trips[i] = TicketTrip(
              id: trip.id,
              userId: trip.userId,
              name: trip.name,
              notes: trip.notes,
              travelDate: trip.travelDate,
              ticketCount: remaining.length,
              tickets: remaining,
              createdAt: trip.createdAt,
              updatedAt: trip.updatedAt,
            );
          }
        }
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ticket deleted')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('$e')));
      _fetchWallet();
    }
  }
}
