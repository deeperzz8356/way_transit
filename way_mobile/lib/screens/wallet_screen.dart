import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../models/booking.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../nav/app_nav.dart';
import 'ticket_detail_screen.dart';

class WalletScreen extends StatefulWidget {
  const WalletScreen({super.key});

  @override
  State<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends State<WalletScreen>
    with SingleTickerProviderStateMixin {
  final _api = ApiService();
  List<Booking> _tickets = [];
  List<UserPassItem> _passes = [];
  bool _isLoading = true;
  String? _error;
  String _modeFilter = 'all';
  String _statusTab = 'active'; // active|used|expired|all
  late TabController _statusTabs;

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

    // ✅ Listen to ticket activation events
    AppNav.ticketActivated.addListener(_onTicketActivated);

    _loadCachedThenFetch();
  }

  @override
  void dispose() {
    _statusTabs.dispose();
    AppNav.ticketActivated.removeListener(_onTicketActivated);
    super.dispose();
  }

  // ✅ Auto-refresh when a ticket is activated
  void _onTicketActivated() {
    print('🔄 Ticket activated! Refreshing wallet...');
    _fetchWallet();
  }

  Color _colorFor(String? hex, String? mode) {
    final raw = (hex != null && hex.isNotEmpty)
        ? hex
        : PlatformColors.forMode(mode);
    final cleaned = raw.replaceFirst('#', '');
    return Color(int.parse('FF$cleaned', radix: 16));
  }

  Future<void> _loadCachedThenFetch() async {
    final prefs = await SharedPreferences.getInstance();
    final cached = prefs.getString('wallet_cache');
    if (cached != null) {
      try {
        final data = WalletData.fromJson(json.decode(cached));
        if (mounted) {
          setState(() {
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
      if (_tickets.isEmpty) _isLoading = true;
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final authService = AuthService(_api); // ✅ Use _api, not new instance
      final isLoggedIn = await authService.ensureAuthLoaded();

      if (!isLoggedIn) {
        if (!mounted) return;
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Please log in first')));
        return;
      }

      final wallet = await _api.getWallet(
        mode: _modeFilter == 'all' ? null : _modeFilter,
      );
      await prefs.setString('wallet_cache', json.encode(wallet.toJson()));

      if (!mounted) return;
      setState(() {
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

  List<Booking> get _filteredTickets {
    final list = _tickets.where((t) {
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
    }).toList();
    list.sort((a, b) {
      if (a.activeBadge != b.activeBadge) {
        return a.activeBadge ? -1 : 1;
      }
      return 0;
    });
    return list;
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
      final authService = AuthService(_api); // ✅ Use _api
      final isLoggedIn = await authService.ensureAuthLoaded();

      if (!isLoggedIn) {
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(const SnackBar(content: Text('Please log in first')));
        }
        return;
      }
      final products = await _api.listPassProducts();
      if (products.isEmpty) return;
      await _api.addPassToWallet(products.first.passId);
      await _fetchWallet();
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Pass added to wallet')));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Could not add pass: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Unified Wallet'),
        actions: [
          IconButton(
            onPressed: _addDemoPass,
            tooltip: 'Add pass',
            icon: const Icon(Icons.card_membership),
          ),
          IconButton(onPressed: _fetchWallet, icon: const Icon(Icons.refresh)),
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
                : _error != null && _tickets.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('Error: $_error', textAlign: TextAlign.center),
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
                          const Text(
                            'Tickets',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                        ],
                        if (_filteredTickets.isEmpty)
                          const Padding(
                            padding: EdgeInsets.symmetric(vertical: 48),
                            child: Center(
                              child: Text(
                                'No tickets in this view.\nAdd a ticket to get started!',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 16,
                                  color: Colors.grey,
                                ),
                              ),
                            ),
                          )
                        else
                          ..._filteredTickets.map(_buildTicketCard),
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
          title: Text(
            pass.name ?? 'Pass',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
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

  Widget _buildTicketCard(Booking ticket) {
    final color = _colorFor(ticket.colorHex, ticket.mode);
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
          final authService = AuthService(_api);
          final isLoggedIn = await authService.ensureAuthLoaded();

          if (!isLoggedIn) {
            if (!mounted) return;
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Please log in first')),
            );
            return;
          }
          await _api.deleteTicket(ticket.id);
          if (!mounted) return;
          setState(() {
            _tickets.removeWhere((t) => t.id == ticket.id);
          });
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(const SnackBar(content: Text('Ticket deleted')));
        } catch (e) {
          if (!mounted) return;
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text('$e')));
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
      child: Card(
        margin: const EdgeInsets.only(bottom: 16),
        elevation: ticket.activeBadge ? 6 : 3,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () async {
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
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
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
                    IconButton(
                      tooltip: 'Delete ticket',
                      onPressed: () => _confirmDelete(ticket),
                      icon: const Icon(Icons.delete_forever, color: Colors.red),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _routeLabel(ticket),
                            style: const TextStyle(
                              fontSize: 17,
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
                          if (ticket.journeyStartedAt != null)
                            Text(
                              'Start: ${ticket.journeyStartedAt!.toLocal().toString().substring(0, 16)}',
                              style: const TextStyle(
                                color: Colors.black54,
                                fontSize: 12,
                              ),
                            ),
                          if (ticket.journeyEstimatedEndAt != null)
                            Text(
                              'Est. end: ${ticket.journeyEstimatedEndAt!.toLocal().toString().substring(0, 16)}',
                              style: const TextStyle(
                                color: Colors.black54,
                                fontSize: 12,
                              ),
                            ),
                          if (ticket.ticketNumber != null &&
                              ticket.ticketNumber!.isNotEmpty)
                            Text(
                              'No: ${ticket.ticketNumber}',
                              style: const TextStyle(color: Colors.black54),
                            ),
                          Text(
                            'Added: ${ticket.bookedAt != null ? ticket.bookedAt!.toLocal().toString().split(' ').first : 'N/A'}',
                            style: const TextStyle(color: Colors.grey),
                          ),
                        ],
                      ),
                    ),
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
      ),
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
      final authService = AuthService(_api);
      final isLoggedIn = await authService.ensureAuthLoaded();

      if (!isLoggedIn) {
        if (!mounted) return;
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Please log in first')));
        return;
      }
      await _api.deleteTicket(ticket.id);
      if (!mounted) return;
      setState(() => _tickets.removeWhere((t) => t.id == ticket.id));
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Ticket deleted')));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      _fetchWallet();
    }
  }
}
