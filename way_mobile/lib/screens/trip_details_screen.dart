import 'package:flutter/material.dart';
import '../models/user_trip.dart';

class TripDetailsScreen extends StatelessWidget {
  final UserTrip trip;

  const TripDetailsScreen({super.key, required this.trip});

  @override
  Widget build(BuildContext context) {
    final modeColor = _modeColor(trip.transportMode);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FE),
      appBar: AppBar(
        title: const Text(
          'Trip Details',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Color(0xFF1A1B35),
          ),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Color(0xFF1A1B35)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header card ──────────────────────────────
            _buildHeaderCard(modeColor),
            const SizedBox(height: 16),

            // ── Journey info ─────────────────────────────
            _buildSection(
              title: 'Journey',
              children: [
                _infoRow(Icons.trip_origin_rounded, 'From', trip.origin),
                _infoRow(Icons.location_on_rounded, 'To', trip.destination),
                if (trip.startedAt != null)
                  _infoRow(
                    Icons.calendar_today_rounded,
                    'Date',
                    _formatDate(trip.startedAt!),
                  ),
                if (trip.startedAt != null)
                  _infoRow(
                    Icons.access_time_rounded,
                    'Start',
                    _formatTime(trip.startedAt!),
                  ),
                if (trip.completedAt != null)
                  _infoRow(
                    Icons.check_circle_outline_rounded,
                    'End',
                    _formatTime(trip.completedAt!),
                  ),
              ],
            ),
            const SizedBox(height: 16),

            // ── Stats ─────────────────────────────────────
            _buildStatsGrid(),
            const SizedBox(height: 16),

            // ── Ticket info ───────────────────────────────
            if (trip.operatorName != null ||
                trip.routeName != null ||
                trip.ticketReference != null)
              _buildSection(
                title: 'Ticket Info',
                children: [
                  if (trip.operatorName != null)
                    _infoRow(
                      Icons.business_rounded,
                      'Operator',
                      trip.operatorName!,
                    ),
                  if (trip.routeName != null)
                    _infoRow(Icons.route_rounded, 'Route', trip.routeName!),
                  if (trip.ticketReference != null)
                    _infoRow(
                      Icons.confirmation_number_rounded,
                      'Reference',
                      trip.ticketReference!,
                    ),
                  if (trip.numTransfers != null && trip.numTransfers! > 0)
                    _infoRow(
                      Icons.transfer_within_a_station_rounded,
                      'Transfers',
                      '${trip.numTransfers}',
                    ),
                ],
              ),
            if (trip.operatorName != null ||
                trip.routeName != null ||
                trip.ticketReference != null)
              const SizedBox(height: 16),

            // ── Legs ─────────────────────────────────────
            if (trip.legs.length > 1) ...[
              _buildLegsSection(),
              const SizedBox(height: 16),
            ],

            // ── Status ───────────────────────────────────
            _buildSection(
              title: 'Status',
              children: [
                Row(
                  children: [
                    _statusDot(trip.status),
                    const SizedBox(width: 10),
                    Text(
                      _statusLabel(trip.status),
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: _statusColor(trip.status),
                        fontSize: 15,
                      ),
                    ),
                  ],
                ),
                if (trip.createdAt != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      'Logged: ${_formatDate(trip.createdAt!)} at ${_formatTime(trip.createdAt!)}',
                      style: const TextStyle(
                        color: Color(0xFF8C90A3),
                        fontSize: 13,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildHeaderCard(Color modeColor) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [modeColor.withValues(alpha: 0.85), modeColor],
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          Text(trip.modeEmoji, style: const TextStyle(fontSize: 44)),
          const SizedBox(height: 12),
          Text(
            trip.modeLabel,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            trip.origin,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Expanded(
                  child: Divider(color: Colors.white.withValues(alpha: 0.4)),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: Icon(
                    Icons.arrow_downward_rounded,
                    color: Colors.white.withValues(alpha: 0.8),
                    size: 20,
                  ),
                ),
                Expanded(
                  child: Divider(color: Colors.white.withValues(alpha: 0.4)),
                ),
              ],
            ),
          ),
          Text(
            trip.destination,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(child: _statCell('📏', 'Distance', trip.formattedDistance)),
          _divider(),
          Expanded(child: _statCell('⏱️', 'Duration', trip.formattedDuration)),
          _divider(),
          Expanded(child: _statCell('💰', 'Fare', trip.formattedFare)),
        ],
      ),
    );
  }

  Widget _statCell(String emoji, String label, String value) {
    return Column(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 22)),
        const SizedBox(height: 6),
        Text(
          value,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1A1B35),
          ),
        ),
        Text(
          label,
          style: const TextStyle(fontSize: 12, color: Color(0xFF8C90A3)),
        ),
      ],
    );
  }

  Widget _divider() {
    return Container(width: 1, height: 56, color: const Color(0xFFEAEBF0));
  }

  Widget _buildSection({
    required String title,
    required List<Widget> children,
  }) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: Color(0xFF8C90A3),
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: const Color(0xFF5974FF)),
          const SizedBox(width: 12),
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                color: Color(0xFF8C90A3),
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 14,
                color: Color(0xFF1A1B35),
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLegsSection() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Trip Legs',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: Color(0xFF8C90A3),
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 12),
          ...trip.legs.asMap().entries.map((entry) {
            final i = entry.key;
            final leg = entry.value;
            final isLast = i == trip.legs.length - 1;
            return _buildLegRow(leg, isLast);
          }),
        ],
      ),
    );
  }

  Widget _buildLegRow(UserTripLeg leg, bool isLast) {
    final legColor = _modeColor(leg.transportMode);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: legColor.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Center(
                child: Text(
                  _modeEmoji(leg.transportMode),
                  style: const TextStyle(fontSize: 14),
                ),
              ),
            ),
            if (!isLast)
              Container(width: 2, height: 40, color: const Color(0xFFE0E3EF)),
          ],
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _modeLegLabel(leg.transportMode),
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: legColor,
                  ),
                ),
                Text(
                  '${leg.origin} → ${leg.destination}',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF1A1B35),
                  ),
                ),
                Text(
                  '${leg.distanceKm?.toStringAsFixed(1) ?? '—'} km  •  ${_legDuration(leg.durationMinutes)}  •  ${_legFare(leg.fare)}',
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
                SizedBox(height: isLast ? 0 : 12),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _statusDot(String status) {
    return Container(
      width: 12,
      height: 12,
      decoration: BoxDecoration(
        color: _statusColor(status),
        shape: BoxShape.circle,
      ),
    );
  }

  // helpers
  String _formatDate(DateTime dt) {
    const months = [
      '',
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
    return '${dt.day.toString().padLeft(2, '0')} ${months[dt.month]} ${dt.year}';
  }

  String _formatTime(DateTime dt) {
    final h = dt.hour % 12 == 0 ? 12 : dt.hour % 12;
    final m = dt.minute.toString().padLeft(2, '0');
    final period = dt.hour < 12 ? 'AM' : 'PM';
    return '$h:$m $period';
  }

  String _legDuration(int? mins) {
    if (mins == null || mins == 0) return '—';
    if (mins < 60) return '${mins}m';
    return '${mins ~/ 60}h ${mins % 60}m';
  }

  String _legFare(double? fare) {
    if (fare == null || fare == 0) return 'Free';
    return '₹${fare.toStringAsFixed(0)}';
  }

  String _statusLabel(String status) {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'cancelled':
        return 'Cancelled';
      case 'started':
        return 'In Progress';
      default:
        return 'Planned';
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'completed':
        return const Color(0xFF22C55E);
      case 'cancelled':
        return const Color(0xFFFF4444);
      case 'started':
        return const Color(0xFFF59E0B);
      default:
        return const Color(0xFF5974FF);
    }
  }

  Color _modeColor(String? mode) {
    switch ((mode ?? 'other').toLowerCase()) {
      case 'walking':
        return const Color(0xFF22C55E);
      case 'bus':
        return const Color(0xFFEF4444);
      case 'train':
      case 'rail':
        return const Color(0xFFB45309);
      case 'metro':
        return const Color(0xFF7C3AED);
      case 'auto':
        return const Color(0xFFF59E0B);
      case 'cab':
        return const Color(0xFF0D9488);
      case 'bike':
        return const Color(0xFF06B6D4);
      case 'car':
        return const Color(0xFF3B82F6);
      default:
        return const Color(0xFF64748B);
    }
  }

  String _modeEmoji(String? mode) {
    switch ((mode ?? 'other').toLowerCase()) {
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

  String _modeLegLabel(String? mode) {
    switch ((mode ?? 'other').toLowerCase()) {
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
