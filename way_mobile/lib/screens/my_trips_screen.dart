import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_trip.dart';
import '../services/api_service.dart';
import '../nav/app_nav.dart';
import 'trip_details_screen.dart';

class MyTripsScreen extends StatefulWidget {
  const MyTripsScreen({super.key});

  @override
  State<MyTripsScreen> createState() => _MyTripsScreenState();
}

class _MyTripsScreenState extends State<MyTripsScreen>
    with SingleTickerProviderStateMixin {
  final ApiService _api = ApiService();
  late TabController _tabController;

  String _selectedPeriod = 'all_time';
  String _selectedStatus = 'all';
  bool _loading = false;
  String? _error;
  List<UserTrip> _trips = [];

  static const _statusOptions = ['all', 'completed', 'planned', 'cancelled'];
  static const _statusLabels = {
    'all': 'All',
    'completed': 'Completed',
    'planned': 'Planned',
    'cancelled': 'Cancelled',
  };

  static const _periodOptions = [
    ('all_time', 'All Time'),
    ('this_week', 'This Week'),
    ('this_month', 'This Month'),
    ('last_3_months', 'Last 3 Months'),
    ('this_year', 'This Year'),
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _statusOptions.length, vsync: this);
    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) {
        setState(() => _selectedStatus = _statusOptions[_tabController.index]);
        _loadTrips();
      }
    });

    // ✅ Listen to ticket activation events
    AppNav.ticketActivated.addListener(_onTicketActivated);

    _loadTrips();
  }

  @override
  void dispose() {
    _tabController.dispose();
    AppNav.ticketActivated.removeListener(_onTicketActivated);
    super.dispose();
  }

  // ✅ Auto-refresh when a ticket is activated (journey started)
  void _onTicketActivated() {
    print('🔄 Ticket activated! Refreshing My Trips...');
    _loadTrips();
  }

  Future<void> _loadTrips() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    // Load token from SharedPreferences and set on API service
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');
      _api.setToken(token);
    } catch (e) {
      print('Failed to load token: $e');
    }

    try {
      final trips = await _api.getTrips(
        status: _selectedStatus != 'all' ? _selectedStatus : null,
        limit: 100,
        offset: 0,
      );

      if (mounted) {
        setState(() {
          _trips = trips;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FE),
      appBar: AppBar(
        title: const Text(
          'My Trips',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Color(0xFF1A1B35),
          ),
        ),
        backgroundColor: Colors.white,
        elevation: 1,
        bottom: TabBar(
          controller: _tabController,
          labelColor: const Color(0xFF5974FF),
          unselectedLabelColor: const Color(0xFF8C90A3),
          indicatorColor: const Color(0xFF5974FF),
          tabs: _statusOptions
              .map((status) => Tab(text: _statusLabels[status]))
              .toList(),
        ),
      ),
      body: Column(
        children: [
          // Period filter
          Padding(
            padding: const EdgeInsets.all(16),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _periodOptions
                    .map(
                      (option) => Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: FilterChip(
                          label: Text(option.$2),
                          selected: _selectedPeriod == option.$1,
                          onSelected: (_) {
                            setState(() => _selectedPeriod = option.$1);
                            _loadTrips();
                          },
                          backgroundColor: Colors.white,
                          selectedColor: const Color(0xFFEBF0FF),
                          labelStyle: TextStyle(
                            color: _selectedPeriod == option.$1
                                ? const Color(0xFF5974FF)
                                : const Color(0xFF8C90A3),
                            fontWeight: FontWeight.w500,
                          ),
                          side: BorderSide(
                            color: _selectedPeriod == option.$1
                                ? const Color(0xFF5974FF)
                                : Colors.grey[300]!,
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
            ),
          ),
          Expanded(child: _buildContent()),
        ],
      ),
    );
  }

  Widget _buildContent() {
    if (_loading) {
      return const Center(
        child: CircularProgressIndicator(color: Color(0xFF5974FF)),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              'Error: $_error',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.red),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loadTrips,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_trips.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.history, size: 64, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              'No trips yet',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w500,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      );
    }

    final grouped = <String, List<UserTrip>>{};
    for (final trip in _trips) {
      if (trip.startedAt != null) {
        final date = _formatDate(trip.startedAt!);
        grouped.putIfAbsent(date, () => []).add(trip);
      }
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: grouped.entries.map((entry) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text(
                entry.key,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF8C90A3),
                ),
              ),
            ),
            ...entry.value.map((trip) => _buildTripCard(trip)).toList(),
            const SizedBox(height: 16),
          ],
        );
      }).toList(),
    );
  }

  Widget _buildTripCard(UserTrip trip) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => TripDetailsScreen(trip: trip),
          ),
        );
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: const Color(0xFFEBF0FF),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Center(
                child: Text(
                  trip.modeEmoji,
                  style: const TextStyle(fontSize: 28),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    trip.modeLabel,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF8C90A3),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${trip.origin} → ${trip.destination}',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF1A1B35),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      if (trip.totalDistanceKm != null &&
                          trip.totalDistanceKm! > 0)
                        Text(
                          '${trip.totalDistanceKm!.toStringAsFixed(1)} km',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                      if (trip.totalDistanceKm != null &&
                          trip.totalDistanceKm! > 0 &&
                          trip.totalDurationMinutes != null &&
                          trip.totalDurationMinutes! > 0)
                        Text(' • ', style: TextStyle(color: Colors.grey[600])),
                      if (trip.totalDurationMinutes != null &&
                          trip.totalDurationMinutes! > 0)
                        Text(
                          trip.formattedDuration,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  trip.formattedFare,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF5974FF),
                  ),
                ),
                if (trip.startedAt != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      _formatTime(trip.startedAt!),
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final date = DateTime(dt.year, dt.month, dt.day);

    if (date == today) {
      return 'Today';
    } else if (date == yesterday) {
      return 'Yesterday';
    } else {
      return '${dt.day} ${_monthName(dt.month)} ${dt.year}';
    }
  }

  String _formatTime(DateTime dt) {
    return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  String _monthName(int month) {
    const months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    return months[month - 1];
  }
}
