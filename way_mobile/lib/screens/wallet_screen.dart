import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../config/api_config.dart';
import '../models/booking.dart';
import '../services/api_service.dart';

class WalletScreen extends StatefulWidget {
  const WalletScreen({super.key});

  @override
  State<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends State<WalletScreen> {
  final _api = ApiService();
  List<Booking> _tickets = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchTickets();
  }

  Future<void> _fetchTickets() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token');
      _api.setToken(token ?? 'dev-token');

      final bookings = await _api.getMyBookings();
      if (!mounted) return;
      setState(() {
        _tickets = bookings;
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Unified Wallet'),
        actions: [
          IconButton(
            onPressed: _fetchTickets,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('Error: $_error', textAlign: TextAlign.center),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: _fetchTickets,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                )
              : _tickets.isEmpty
                  ? const Center(
                      child: Text(
                        'Your wallet is empty.\nAdd a ticket to get started!',
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 18, color: Colors.grey),
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _fetchTickets,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _tickets.length,
                        itemBuilder: (context, index) {
                          final ticket = _tickets[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 16),
                            elevation: 4,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          _routeLabel(ticket),
                                          style: const TextStyle(
                                            fontSize: 18,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                        const SizedBox(height: 8),
                                        Text(
                                          'Status: ${ticket.status}',
                                          style: const TextStyle(
                                            color: Colors.green,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          'Added: ${ticket.bookedAt != null ? ticket.bookedAt!.toLocal().toString().split(' ').first : 'N/A'}',
                                          style: const TextStyle(color: Colors.grey),
                                        ),
                                        if (ticket.imageUrl != null &&
                                            ticket.imageUrl!.isNotEmpty) ...[
                                          const SizedBox(height: 8),
                                          ClipRRect(
                                            borderRadius: BorderRadius.circular(8),
                                            child: Image.network(
                                              ApiConfig.resolveUrl(ticket.imageUrl!),
                                              height: 72,
                                              width: 96,
                                              fit: BoxFit.cover,
                                              errorBuilder: (_, error, stackTrace) =>
                                                  const SizedBox.shrink(),
                                            ),
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                  if (ticket.ticketCode != null)
                                    Column(
                                      children: [
                                        QrImageView(
                                          data: ticket.ticketCode!,
                                          version: QrVersions.auto,
                                          size: 80.0,
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          ticket.ticketCode!
                                              .substring(
                                                0,
                                                ticket.ticketCode!.length >= 8
                                                    ? 8
                                                    : ticket.ticketCode!.length,
                                              )
                                              .toUpperCase(),
                                          style: const TextStyle(
                                            fontSize: 12,
                                            fontFamily: 'monospace',
                                            color: Colors.grey,
                                          ),
                                        ),
                                      ],
                                    ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}
