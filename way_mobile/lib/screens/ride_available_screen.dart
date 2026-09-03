import 'package:flutter/material.dart';
import '../models/ride.dart';
import 'ride_booking_screen.dart';

class RideAvailableScreen extends StatefulWidget {
  final String source;
  final String destination;
  final String vehicleType;
  final List<Ride> rides;

  const RideAvailableScreen({
    super.key,
    required this.source,
    required this.destination,
    required this.vehicleType,
    required this.rides,
  });

  @override
  State<RideAvailableScreen> createState() => _RideAvailableScreenState();
}

class _RideAvailableScreenState extends State<RideAvailableScreen> {
  late List<Ride> _filteredRides;

  @override
  void initState() {
    super.initState();
    _filteredRides = widget.rides
        .where((ride) => ride.vehicleType == widget.vehicleType)
        .toList();
  }

  String _getVehicleEmoji(String type) {
    switch (type) {
      case 'bike':
        return '🏍️';
      case 'auto':
        return '🚙';
      case 'premium':
        return '🚙';
      default:
        return '🚗';
    }
  }

  Color _getVehicleColor(String type) {
    switch (type) {
      case 'bike':
        return const Color(0xFFFF6B6B);
      case 'auto':
        return const Color(0xFFFFA500);
      case 'premium':
        return const Color(0xFF6C5CE7);
      default:
        return const Color(0xFF5974FF);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FE),
      appBar: AppBar(
        title: const Text('Available Rides'),
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Route info
            Container(
              color: Colors.white,
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'From',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              widget.source,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF1A1B35),
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      const Icon(Icons.arrow_forward, color: Color(0xFF5974FF)),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'To',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              widget.destination,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF1A1B35),
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Rides list
            Expanded(
              child: _filteredRides.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text(
                            'No rides available',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF1A1B35),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Try searching with different parameters',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _filteredRides.length,
                      itemBuilder: (context, index) {
                        final ride = _filteredRides[index];
                        return _buildRideCard(context, ride);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRideCard(BuildContext context, Ride ride) {
    final color = _getVehicleColor(ride.vehicleType);
    final emoji = _getVehicleEmoji(ride.vehicleType);

    return GestureDetector(
      onTap: () {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => RideBookingScreen(ride: ride),
          ),
        );
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          children: [
            // Driver info row
            Row(
              children: [
                // Driver avatar
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Center(
                    child: Text(emoji, style: const TextStyle(fontSize: 32)),
                  ),
                ),
                const SizedBox(width: 16),

                // Driver details
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        ride.driverName ?? 'Unknown Driver',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1A1B35),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(Icons.star, size: 14, color: Color(0xFFFFA500)),
                          const SizedBox(width: 4),
                          Text(
                            '${ride.driverRating?.toStringAsFixed(1) ?? "N/A"} (${ride.driverReviews} trips)',
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

                // Fare
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '₹${ride.fare.toStringAsFixed(0)}',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF5974FF),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${ride.estimatedMinutes} min',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ],
            ),

            const SizedBox(height: 12),

            // Vehicle info
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    ride.vehicleType.toUpperCase(),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    ride.vehiclePlate ?? 'N/A',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Colors.grey[700],
                    ),
                  ),
                ),
                const Spacer(),
                const Icon(Icons.arrow_forward, color: Color(0xFF5974FF)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
