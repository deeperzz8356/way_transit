import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../models/booking.dart';
import '../nav/app_nav.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
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
  bool _selectMode = false;
  bool _isUpdatingCollection = false;
  String? _error;

  String _modeFilter = 'all';
  String _statusTab = 'active';

  late final TabController _statusTabs;

  final Set<int> _selectedIds = {};
  final Set<int> _expandedTripIds = {};
  final Set<int> _deletingIds = {};

  int _fetchVersion = 0;

  static const _modes = ['all', 'rail', 'metro', 'bus', 'cab'];
  static const _statuses = ['active', 'used', 'expired', 'all'];

  @override
  void initState() {
    super.initState();

    _statusTabs = TabController(length: _statuses.length, vsync: this);
    _statusTabs.addListener(_onStatusChanged);
    AppNav.ticketActivated.addListener(_onTicketActivated);

    _loadCachedThenFetch();
  }

  @override
  void dispose() {
    _statusTabs.removeListener(_onStatusChanged);
    _statusTabs.dispose();
    AppNav.ticketActivated.removeListener(_onTicketActivated);
    super.dispose();
  }

  void _onStatusChanged() {
    if (!mounted || _statusTabs.indexIsChanging) return;

    final status = _statuses[_statusTabs.index];
    if (status == _statusTab) return;

    setState(() => _statusTab = status);
  }

  void _onTicketActivated() {
    _fetchWallet();
  }

  void _showMessage(String message) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Color _colorFor(String? hex, String? mode) {
    final raw = hex != null && hex.isNotEmpty
        ? hex
        : PlatformColors.forMode(mode);
    final cleaned = raw.replaceFirst('#', '');

    final value = int.tryParse(
      cleaned.length == 6 ? 'FF$cleaned' : cleaned,
      radix: 16,
    );

    return value == null ? Colors.blueGrey : Color(value);
  }

  Future<bool> _ensureAuth() async {
    final isLoggedIn = await AuthService(_api).ensureAuthLoaded();
    if (!mounted) return false;

    if (!isLoggedIn) {
      setState(() {
        _isLoading = false;
        _error = 'Please log in first';
        _trips = [];
        _tickets = [];
        _passes = [];
        _selectedIds.clear();
        _selectMode = false;
      });
      _showMessage('Please log in first');
      return false;
    }

    return true;
  }

  Future<void> _loadCachedThenFetch() async {
    try {
      if (!await _ensureAuth()) return;

      final prefs = await SharedPreferences.getInstance();
      if (!mounted) return;

      final cached = prefs.getString('wallet_cache');
      if (cached != null) {
        try {
          final data = WalletData.fromJson(json.decode(cached));
          setState(() {
            _trips = data.trips;
            _tickets = data.tickets;
            _passes = data.passes;
            _isLoading = false;
          });
        } catch (_) {
          // Fetch fresh data if the cached wallet cannot be read.
        }
      }
    } catch (_) {
      // Let the normal fetch report authentication or network failures.
    }

    if (mounted) {
      await _fetchWallet();
    }
  }

  Future<void> _fetchWallet() async {
    if (!mounted) return;

    final version = ++_fetchVersion;
    final mode = _modeFilter;

    setState(() {
      _error = null;
      if (_tickets.isEmpty && _trips.isEmpty && _passes.isEmpty) {
        _isLoading = true;
      }
    });

    try {
      if (!await _ensureAuth()) return;

      final wallet = await _api.getWallet(
        mode: mode == 'all' ? null : mode,
      );

      if (!mounted || version != _fetchVersion) return;

      setState(() {
        _trips = wallet.trips;
        _tickets = wallet.tickets;
        _passes = wallet.passes;
        _isLoading = false;

        final availableIds = <int>{
          ..._tickets.map((ticket) => ticket.id),
          for (final trip in _trips)
            ...trip.tickets.map((ticket) => ticket.id),
        };
        _selectedIds.retainAll(availableIds);
      });

      // Cache the complete wallet, rather than a single transport filter.
      if (mode == 'all') {
        try {
          final prefs = await SharedPreferences.getInstance();
          if (!mounted || version != _fetchVersion) return;
          await prefs.setString(
            'wallet_cache',
            json.encode(wallet.toJson()),
          );
        } catch (_) {
          // A cache failure should not hide a successfully loaded wallet.
        }
      }
    } catch (e) {
      if (!mounted || version != _fetchVersion) return;

      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  bool _matchesStatus(Booking ticket) {
    final status = ticket.status.toUpperCase();

    switch (_statusTab) {
      case 'active':
        return status == 'CONFIRMED' || status == 'IN_PROGRESS';
      case 'used':
        return status == 'USED';
      case 'expired':
        return status == 'EXPIRED';
      default:
        return true;
    }
  }

  List<Booking> _filterTickets(List<Booking> tickets) {
    final result = tickets.where(_matchesStatus).toList();

    result.sort((a, b) {
      if (a.activeBadge == b.activeBadge) return 0;
      return a.activeBadge ? -1 : 1;
    });

    return result;
  }

  List<Booking> get _filteredUngrouped => _filterTickets(_tickets);

  List<TicketTrip> get _visibleTrips {
    return _trips.where((trip) {
      return trip.tickets.isEmpty ||
          _filterTickets(trip.tickets).isNotEmpty;
    }).toList();
  }

  String _routeLabel(Booking ticket) {
    final source = ticket.source?.trim();
    final destination = ticket.destination?.trim();

    return '${source?.isNotEmpty == true ? source : 'Unknown'} ➔ '
        '${destination?.isNotEmpty == true ? destination : 'Unknown'}';
  }

  String _dateLabel(DateTime value) {
    return value.toLocal().toString().split(' ').first;
  }

  String _dateTimeLabel(DateTime value) {
    return value.toLocal().toString().substring(0, 16);
  }

  Future<void> _addDemoPass() async {
    try {
      if (!await _ensureAuth()) return;

      final products = await _api.listPassProducts();
      if (!mounted) return;

      if (products.isEmpty) {
        _showMessage('No passes are available');
        return;
      }

      await _api.addPassToWallet(products.first.passId);
      if (!mounted) return;

      await _fetchWallet();
      _showMessage('Pass added to wallet');
    } catch (e) {
      _showMessage('Could not add pass: $e');
    }
  }

  void _exitSelectMode() {
    if (!mounted) return;

    setState(() {
      _selectMode = false;
      _selectedIds.clear();
    });
  }

  Future<void> _openTrip(TicketTrip trip) async {
    if (!mounted) return;

    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => TripDetailScreen(trip: trip),
      ),
    );

    if (mounted) {
      await _fetchWallet();
    }
  }

  Future<Map<String, String>?> _showCollectionForm() async {
    final nameController = TextEditingController();
    final notesController = TextEditingController();
    final formKey = GlobalKey<FormState>();
    DateTime? travelDate;

    try {
      return await showDialog<Map<String, String>>(
        context: context,
        builder: (dialogContext) {
          return StatefulBuilder(
            builder: (context, setDialogState) {
              return AlertDialog(
                title: const Text('New collection'),
                content: SingleChildScrollView(
                  child: Form(
                    key: formKey,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        TextFormField(
                          controller: nameController,
                          autofocus: true,
                          textCapitalization: TextCapitalization.sentences,
                          decoration: const InputDecoration(
                            labelText: 'Collection name',
                            hintText: 'Mumbai weekend',
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return 'Enter a collection name';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 12),
                        TextFormField(
                          controller: notesController,
                          minLines: 1,
                          maxLines: 3,
                          decoration: const InputDecoration(
                            labelText: 'Notes (optional)',
                          ),
                        ),
                        const SizedBox(height: 12),
                        OutlinedButton.icon(
                          icon: const Icon(Icons.calendar_today),
                          label: Text(
                            travelDate == null
                                ? 'Travel date (optional)'
                                : _dateLabel(travelDate!),
                          ),
                          onPressed: () async {
                            final now = DateTime.now();
                            final chosen = await showDatePicker(
                              context: dialogContext,
                              initialDate: travelDate ?? now,
                              firstDate: DateTime(2000),
                              lastDate: DateTime(2100, 12, 31),
                            );

                            if (!dialogContext.mounted || chosen == null) {
                              return;
                            }

                            setDialogState(() => travelDate = chosen);
                          },
                        ),
                        if (travelDate != null)
                          TextButton(
                            onPressed: () {
                              setDialogState(() => travelDate = null);
                            },
                            child: const Text('Clear date'),
                          ),
                      ],
                    ),
                  ),
                ),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(dialogContext),
                    child: const Text('Cancel'),
                  ),
                  FilledButton(
                    onPressed: () {
                      if (!formKey.currentState!.validate()) return;

                      Navigator.pop(dialogContext, <String, String>{
                        'name': nameController.text.trim(),
                        if (notesController.text.trim().isNotEmpty)
                          'notes': notesController.text.trim(),
                        if (travelDate != null)
                          'travelDate':
                              travelDate!.toIso8601String().split('T').first,
                      });
                    },
                    child: const Text('Continue'),
                  ),
                ],
              );
            },
          );
        },
      );
    } finally {
      // Wait for the dialog's exit transition before disposing its fields.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        nameController.dispose();
        notesController.dispose();
      });
    }
  }

  Future<List<int>?> _chooseTicketsForCollection() async {
    if (_tickets.isEmpty) return <int>[];

    final selected = <int>{};

    return showDialog<List<int>>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('Add tickets'),
              content: SizedBox(
                width: double.maxFinite,
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text(
                        'Choose tickets for this collection, '
                        'or create it empty.',
                      ),
                      const SizedBox(height: 12),
                      for (final ticket in _tickets)
                        CheckboxListTile(
                          contentPadding: EdgeInsets.zero,
                          value: selected.contains(ticket.id),
                          title: Text(_routeLabel(ticket)),
                          subtitle: Text(ticket.status),
                          onChanged: (checked) {
                            setDialogState(() {
                              if (checked == true) {
                                selected.add(ticket.id);
                              } else {
                                selected.remove(ticket.id);
                              }
                            });
                          },
                        ),
                    ],
                  ),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(dialogContext),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: () {
                    Navigator.pop(dialogContext, selected.toList());
                  },
                  child: Text(
                    selected.isEmpty
                        ? 'Create empty'
                        : 'Create with ${selected.length} tickets',
                  ),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _createTrip() async {
    if (_isUpdatingCollection) return;

    setState(() => _isUpdatingCollection = true);

    try {
      if (!await _ensureAuth()) return;

      final data = await _showCollectionForm();
      if (!mounted || data == null) return;

      final ticketIds = await _chooseTicketsForCollection();
      if (!mounted || ticketIds == null) return;

      if (!await _ensureAuth()) return;

      final created = await _api.createTrip(
        name: data['name']!,
        notes: data['notes'],
        travelDate: data['travelDate'],
      );

      if (ticketIds.isNotEmpty) {
        try {
          await _api.addTicketsToTrip(created.id, ticketIds);
        } catch (e) {
          await _fetchWallet();
          _showMessage(
            'Collection created, but tickets could not be added: $e',
          );
          return;
        }
      }

      await _fetchWallet();
      if (!mounted) return;

      _showMessage('Collection "${created.name}" created');

      final matches = _trips.where((trip) => trip.id == created.id);
      await _openTrip(matches.isEmpty ? created : matches.first);
    } catch (e) {
      _showMessage('Could not create collection: $e');
    } finally {
      if (mounted) {
        setState(() => _isUpdatingCollection = false);
      }
    }
  }

  Future<void> _addSelectedToTrip() async {
    if (_selectedIds.isEmpty || _isUpdatingCollection) return;

    final ticketIds = _selectedIds.toList();
    setState(() => _isUpdatingCollection = true);

    try {
      if (!await _ensureAuth()) return;

      // A string distinguishes "create" from an existing collection ID.
      final choice = await showDialog<String>(
        context: context,
        builder: (dialogContext) {
          return SimpleDialog(
            title: const Text('Add to collection'),
            children: [
              SimpleDialogOption(
                onPressed: () => Navigator.pop(dialogContext, 'create'),
                child: const Row(
                  children: [
                    Icon(Icons.create_new_folder_outlined),
                    SizedBox(width: 12),
                    Text('New collection'),
                  ],
                ),
              ),
              for (final trip in _trips)
                SimpleDialogOption(
                  onPressed: () {
                    Navigator.pop(dialogContext, trip.id.toString());
                  },
                  child: Text(trip.name),
                ),
            ],
          );
        },
      );

      if (!mounted || choice == null) return;

      int tripId;

      if (choice == 'create') {
        final data = await _showCollectionForm();
        if (!mounted || data == null) return;

        if (!await _ensureAuth()) return;

        final trip = await _api.createTrip(
          name: data['name']!,
          notes: data['notes'],
          travelDate: data['travelDate'],
        );
        tripId = trip.id;
      } else {
        tripId = int.parse(choice);
        if (!await _ensureAuth()) return;
      }

      await _api.addTicketsToTrip(tripId, ticketIds);
      if (!mounted) return;

      _exitSelectMode();
      await _fetchWallet();
      _showMessage('Tickets added to collection');
    } catch (e) {
      _showMessage('Could not add tickets: $e');
      if (mounted) {
        await _fetchWallet();
      }
    } finally {
      if (mounted) {
        setState(() => _isUpdatingCollection = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final visibleTrips = _visibleTrips;
    final ungrouped = _filteredUngrouped;
    final hasContent =
        _passes.isNotEmpty ||
        visibleTrips.isNotEmpty ||
        ungrouped.isNotEmpty;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          _selectMode
              ? '${_selectedIds.length} selected'
              : 'My Unified Wallet',
        ),
        leading: _selectMode
            ? IconButton(
                icon: const Icon(Icons.close),
                onPressed: _isUpdatingCollection ? null : _exitSelectMode,
              )
            : null,
        actions: [
          if (_selectMode)
            TextButton(
              onPressed:
                  _selectedIds.isEmpty || _isUpdatingCollection
                  ? null
                  : _addSelectedToTrip,
              child: Text(
                _isUpdatingCollection ? 'Adding…' : 'Add to collection',
              ),
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
              tooltip: 'Refresh wallet',
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
              onPressed: _isUpdatingCollection ? null : _createTrip,
              icon: const Icon(Icons.create_new_folder_outlined),
              label: Text(
                _isUpdatingCollection ? 'Creating…' : 'New collection',
              ),
            ),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
            child: Row(
              children: _modes.map((mode) {
                final color = _colorFor(
                  null,
                  mode == 'all' ? 'other' : mode,
                );

                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    selected: _modeFilter == mode,
                    label: Text(mode.toUpperCase()),
                    selectedColor: color.withOpacity(0.25),
                    checkmarkColor: color,
                    onSelected: (_) {
                      setState(() => _modeFilter = mode);
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
                          Text(
                            'Error: $_error',
                            textAlign: TextAlign.center,
                          ),
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
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.all(16),
                      children: [
                        if (_error != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: Text(
                              'Could not refresh: $_error',
                              style: const TextStyle(color: Colors.red),
                            ),
                          ),
                        if (_passes.isNotEmpty) ...[
                          _sectionTitle('Passes'),
                          ..._passes.map(_buildPassCard),
                          const SizedBox(height: 16),
                        ],
                        if (visibleTrips.isNotEmpty) ...[
                          _sectionTitle('Collections'),
                          ...visibleTrips.map(_buildTripSection),
                          const SizedBox(height: 16),
                        ] else if (!_selectMode)
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
                                    'Example: “Mumbai weekend” with '
                                    'train + metro + cab tickets.',
                                    style: TextStyle(
                                      color: Colors.grey.shade700,
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  ElevatedButton.icon(
                                    onPressed: _isUpdatingCollection
                                        ? null
                                        : _createTrip,
                                    icon: const Icon(Icons.add),
                                    label: const Text('Create collection'),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        if (ungrouped.isNotEmpty) ...[
                          _sectionTitle(
                            _trips.isNotEmpty || _passes.isNotEmpty
                                ? 'Other tickets'
                                : 'Tickets',
                          ),
                          ...ungrouped.map(
                            (ticket) => _buildTicketCard(ticket),
                          ),
                        ] else if (visibleTrips.isEmpty && _passes.isEmpty)
                          const Padding(
                            padding: EdgeInsets.symmetric(vertical: 48),
                            child: Center(
                              child: Text(
                                'No tickets in this view.\n'
                                'Create a collection or add a ticket!',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 16,
                                  color: Colors.grey,
                                ),
                              ),
                            ),
                          ),
                        const SizedBox(height: 88),
                      ],
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.bold,
        ),
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
          title: Text(
            pass.name ?? 'Pass',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          subtitle: Text(
            '${(pass.modeCoverage ?? 'other').toUpperCase()} · '
            '${pass.status}'
            '${pass.validUntil != null ? ' · until ${_dateLabel(pass.validUntil!)}' : ''}',
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
    final expanded =
        _expandedTripIds.contains(trip.id) || trip.tickets.isEmpty;

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
                  : '${filtered.length} '
                      'ticket${filtered.length == 1 ? '' : 's'}'
                      '${trip.travelDate != null ? ' · ${trip.travelDate}' : ''}',
            ),
            trailing: Icon(
              _selectMode
                  ? expanded
                        ? Icons.expand_less
                        : Icons.expand_more
                  : Icons.chevron_right,
            ),
            onTap: () {
              if (_selectMode) {
                setState(() {
                  if (!_expandedTripIds.add(trip.id)) {
                    _expandedTripIds.remove(trip.id);
                  }
                });
              } else {
                _openTrip(trip);
              }
            },
          ),
          if (expanded && filtered.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
              child: Column(
                children: filtered
                    .map((ticket) => _buildTicketCard(ticket, compact: true))
                    .toList(),
              ),
            ),
          if (expanded && trip.tickets.isEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: OutlinedButton.icon(
                onPressed: () => _openTrip(trip),
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
    final deleting = _deletingIds.contains(ticket.id);

    final cardBody = Card(
      margin: EdgeInsets.only(bottom: compact ? 8 : 16),
      elevation: ticket.activeBadge ? 6 : 3,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onLongPress: deleting || _isUpdatingCollection
            ? null
            : () {
                setState(() {
                  _selectMode = true;
                  _selectedIds.add(ticket.id);
                });
              },
        onTap: deleting || _isUpdatingCollection
            ? null
            : () async {
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

                if (mounted) {
                  await _fetchWallet();
                }
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
                            horizontal: 8,
                            vertical: 2,
                          ),
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
                              horizontal: 8,
                              vertical: 3,
                            ),
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
                      onPressed: deleting
                          ? null
                          : () => _confirmDelete(ticket),
                      icon: deleting
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                              ),
                            )
                          : const Icon(
                              Icons.delete_forever,
                              color: Colors.red,
                            ),
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
                                : ticket.status.toUpperCase() == 'USED'
                                ? Colors.grey
                                : Colors.green,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        if (!compact) ...[
                          if (ticket.journeyStartedAt != null)
                            Text(
                              'Start: '
                              '${_dateTimeLabel(ticket.journeyStartedAt!)}',
                              style: const TextStyle(
                                color: Colors.black54,
                                fontSize: 12,
                              ),
                            ),
                          if (ticket.journeyEstimatedEndAt != null)
                            Text(
                              'Est. end: '
                              '${_dateTimeLabel(ticket.journeyEstimatedEndAt!)}',
                              style: const TextStyle(
                                color: Colors.black54,
                                fontSize: 12,
                              ),
                            ),
                          if (ticket.ticketNumber != null &&
                              ticket.ticketNumber!.isNotEmpty)
                            Text(
                              'No: ${ticket.ticketNumber}',
                              style: const TextStyle(
                                color: Colors.black54,
                              ),
                            ),
                          Text(
                            'Added: '
                            '${ticket.bookedAt != null ? _dateLabel(ticket.bookedAt!) : 'N/A'}',
                            style: const TextStyle(color: Colors.grey),
                          ),
                        ],
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
                              ? ticket.displayQr
                                    .substring(0, 8)
                                    .toUpperCase()
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
      direction: deleting
          ? DismissDirection.none
          : DismissDirection.endToStart,
      confirmDismiss: (_) => _confirmAndDeleteOnServer(ticket),
      onDismissed: (_) {
        if (!mounted) return;
        _removeTicketLocally(ticket.id);
        _showMessage('Ticket deleted');
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

  Future<bool> _confirmAndDeleteOnServer(Booking ticket) async {
    if (_deletingIds.contains(ticket.id)) return false;

    setState(() => _deletingIds.add(ticket.id));

    try {
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Delete ticket?'),
          content: Text(
            'Remove ${_routeLabel(ticket)} from your wallet?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              style: TextButton.styleFrom(
                foregroundColor: Colors.red,
              ),
              child: const Text('Delete'),
            ),
          ],
        ),
      );

      if (!mounted || confirmed != true) return false;
      if (!await _ensureAuth()) return false;

      await _api.deleteTicket(ticket.id);

      // Prevent an old cached wallet from restoring the deleted ticket.
      try {
        final prefs = await SharedPreferences.getInstance();
        await prefs.remove('wallet_cache');
      } catch (_) {
        // The ticket was still successfully deleted on the server.
      }

      return mounted;
    } catch (e) {
      _showMessage('Could not delete ticket: $e');
      return false;
    } finally {
      if (mounted) {
        setState(() => _deletingIds.remove(ticket.id));
      }
    }
  }

  void _removeTicketLocally(int ticketId) {
    if (!mounted) return;

    setState(() {
      _tickets.removeWhere((ticket) => ticket.id == ticketId);
      _selectedIds.remove(ticketId);

      for (var i = 0; i < _trips.length; i++) {
        final trip = _trips[i];
        if (!trip.tickets.any((ticket) => ticket.id == ticketId)) {
          continue;
        }

        final remaining = trip.tickets
            .where((ticket) => ticket.id != ticketId)
            .toList();

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
    });
  }

  Future<void> _confirmDelete(Booking ticket) async {
    final deleted = await _confirmAndDeleteOnServer(ticket);
    if (!mounted || !deleted) return;

    _removeTicketLocally(ticket.id);
    _showMessage('Ticket deleted');
  }
}