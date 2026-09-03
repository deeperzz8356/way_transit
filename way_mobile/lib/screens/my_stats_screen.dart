import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_trip.dart';
import '../services/api_service.dart';
import '../nav/app_nav.dart';

class MyStatsScreen extends StatefulWidget {
  const MyStatsScreen({super.key});

  @override
  State<MyStatsScreen> createState() => _MyStatsScreenState();
}

class _MyStatsScreenState extends State<MyStatsScreen> {
  final ApiService _api = ApiService();

  String _selectedPeriod = 'all_time';
  bool _loading = false;
  String? _error;
  TravelStatsOverview? _stats;

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
    // ✅ Listen to ticket activation events
    AppNav.ticketActivated.addListener(_onTicketActivated);
    _loadStats();
  }

  @override
  void dispose() {
    AppNav.ticketActivated.removeListener(_onTicketActivated);
    super.dispose();
  }

  // ✅ Auto-refresh when a ticket is activated (journey started)
  void _onTicketActivated() {
    print('🔄 Ticket activated! Refreshing My Stats...');
    _loadStats();
  }

  Future<void> _loadStats() async {
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
      final stats = await _api.getTravelStats(period: _selectedPeriod);
      if (mounted) {
        setState(() {
          _stats = stats;
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
          'My Stats',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Color(0xFF1A1B35),
          ),
        ),
        backgroundColor: Colors.white,
        elevation: 1,
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF5974FF)),
            )
          : _error != null
          ? Center(
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
                    onPressed: _loadStats,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                  ),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  // Period selector
                  SingleChildScrollView(
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
                                  _loadStats();
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
                  const SizedBox(height: 20),
                  if (_stats != null) ...[
                    // Overview stats
                    _buildOverviewCards(),
                    const SizedBox(height: 24),

                    // By transport mode
                    if (_stats!.byMode.isNotEmpty) ...[
                      _buildSection(
                        title: 'By Transport Mode',
                        children: [
                          ..._stats!.byMode.map(
                            (mode) => _buildModeStatItem(mode),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                    ],

                    // Green travel
                    _buildGreenTravelSection(),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _buildOverviewCards() {
    return GridView.count(
      crossAxisCount: 2,
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      children: [
        _buildStatCard(
          label: 'Total Trips',
          value: _stats!.totalTrips.toString(),
          icon: Icons.receipt,
        ),
        _buildStatCard(
          label: 'Total Distance',
          value: '${_stats!.totalDistanceKm.toStringAsFixed(1)} km',
          icon: Icons.map,
        ),
        _buildStatCard(
          label: 'Total Time',
          value: _stats!.formattedTotalTime,
          icon: Icons.schedule,
        ),
        _buildStatCard(
          label: 'Total Spent',
          value: _stats!.formattedFare,
          icon: Icons.payments,
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required String label,
    required String value,
    required IconData icon,
  }) {
    return Container(
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
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Icon(icon, size: 32, color: const Color(0xFF5974FF)),
          const SizedBox(height: 12),
          Text(
            value,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1A1B35),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildModeStatItem(TransportModeStats mode) {
    String modeEmoji(String mode) {
      switch (mode.toLowerCase()) {
        case 'walking':
          return '🚶';
        case 'bus':
          return '🚌';
        case 'train':
        case 'rail':
          return '🚆';
        case 'metro':
          return '🚇';
        case 'auto':
          return '🛺';
        case 'cab':
          return '🚕';
        case 'bike':
          return '🚲';
        case 'car':
          return '🚗';
        default:
          return '🚍';
      }
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF0F2F7),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Text(
            modeEmoji(mode.transportMode),
            style: const TextStyle(fontSize: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _modeLabel(mode.transportMode),
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF1A1B35),
                  ),
                ),
                Text(
                  '${mode.tripCount} trips • ${mode.totalDistanceKm.toStringAsFixed(1)} km',
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '₹${mode.totalFare.toStringAsFixed(0)}',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF5974FF),
                ),
              ),
              Text(
                '${mode.totalDurationMinutes ~/ 60}h ${mode.totalDurationMinutes % 60}m',
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildGreenTravelSection() {
    final green = _stats!.green;
    return _buildSection(
      title: '🌱 Green Travel',
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.green[50],
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.green[200]!),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _greenStatRow(
                'CO₂ Emissions',
                '${green.totalCo2Kg.toStringAsFixed(2)} kg',
                '📉',
              ),
              const SizedBox(height: 12),
              _greenStatRow(
                'CO₂ Saved vs Car',
                '${green.co2SavedVsCarKg.toStringAsFixed(2)} kg',
                '✨',
              ),
              const SizedBox(height: 12),
              _greenStatRow(
                'Walking Distance',
                '${green.walkingDistanceKm.toStringAsFixed(1)} km',
                '🚶',
              ),
              const SizedBox(height: 12),
              _greenStatRow(
                'Public Transport',
                '${green.publicTransportDistanceKm.toStringAsFixed(1)} km',
                '🚌',
              ),
              if (green.greenestMode != null) ...[
                const SizedBox(height: 12),
                _greenStatRow(
                  'Greenest Mode',
                  _modeLabel(green.greenestMode ?? 'other'),
                  '🌿',
                ),
              ],
              const SizedBox(height: 12),
              Text(
                green.note,
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.grey[600],
                  fontStyle: FontStyle.italic,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _greenStatRow(String label, String value, String icon) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Text(icon, style: const TextStyle(fontSize: 16)),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(fontSize: 13, color: Color(0xFF1A1B35)),
            ),
          ],
        ),
        Text(
          value,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: Color(0xFF5974FF),
          ),
        ),
      ],
    );
  }

  Widget _buildSection({
    required String title,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1A1B35),
          ),
        ),
        const SizedBox(height: 12),
        ...children,
      ],
    );
  }

  String _modeLabel(String mode) {
    switch (mode.toLowerCase()) {
      case 'walking':
        return 'Walking';
      case 'bus':
        return 'Bus';
      case 'train':
      case 'rail':
        return 'Train';
      case 'metro':
        return 'Metro';
      case 'auto':
        return 'Auto';
      case 'cab':
        return 'Cab';
      case 'bike':
        return 'Bike';
      case 'car':
        return 'Car';
      default:
        return 'Other';
    }
  }
}
