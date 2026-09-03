import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'dart:async';
import '../models/ride.dart';

class RideTrackingScreen extends StatefulWidget {
  final Ride ride;

  const RideTrackingScreen({super.key, required this.ride});

  @override
  State<RideTrackingScreen> createState() => _RideTrackingScreenState();
}

class _RideTrackingScreenState extends State<RideTrackingScreen> {
  late final MapController _mapController;
  late Ride _ride;
  late Timer _locationUpdateTimer;
  double _driverLat = 19.0760;
  double _driverLon = 72.8777;

  @override
  void initState() {
    super.initState();
    _mapController = MapController();
    _ride = widget.ride;
    
    // Simulate driver location updates
    _locationUpdateTimer = Timer.periodic(const Duration(seconds: 3), (_) {
      setState(() {
        _driverLat += (DateTime.now().millisecond % 100 - 50) / 10000;
        _driverLon += (DateTime.now().millisecond % 100 - 50) / 10000;
      });
    });
  }

  @override
  void dispose() {
    _locationUpdateTimer.cancel();
    super.dispose();
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
    final color = _getVehicleColor(_ride.vehicleType);
    final emoji = _getVehicleEmoji(_ride.vehicleType);

    return WillPopScope(
      onWillPop: () async => false,
      child: Scaffold(
        body: Stack(
          children: [
            // Map
            FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                center: LatLng(_driverLat, _driverLon),
                zoom: 15.0,
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.example.way_mobile',
                ),
                MarkerLayer(
                  markers: [
                    // Driver marker
                    Marker(
                      point: LatLng(_driverLat, _driverLon),
                      width: 50,
                      height: 50,
                      child: Container(
                        decoration: BoxDecoration(
                          color: color,
                          borderRadius: BorderRadius.circular(25),
                          border: Border.all(color: Colors.white, width: 3),
                          boxShadow: [
                            BoxShadow(
                              color: color.withOpacity(0.4),
                              blurRadius: 10,
                            ),
                          ],
                        ),
                        child: Center(
                          child: Text(emoji, style: const TextStyle(fontSize: 24)),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),

            // Top info card
            Positioned(
              top: 20,
              left: 20,
              right: 20,
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.1),
                      blurRadius: 20,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Driver arriving in ${_ride.estimatedMinutes} min',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1A1B35),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _ride.driverName ?? 'Unknown Driver',
                      style: const TextStyle(
                        fontSize: 14,
                        color: Color(0xFF8C90A3),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(Icons.phone, size: 16, color: color),
                        const SizedBox(width: 8),
                        Text(
                          _ride.driverPhone ?? 'N/A',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            // Bottom tracking card
            Positioned(
              bottom: 20,
              left: 20,
              right: 20,
              child: Column(
                children: [
                  // OTP Card
                  if (_ride.otp != null)
                    Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFF8DC),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFFFA500), width: 1.5),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Show this code to driver',
                            style: TextStyle(
                              fontSize: 12,
                              color: Color(0xFFFFA500),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 24,
                                  vertical: 12,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(
                                  _ride.otp!,
                                  style: const TextStyle(
                                    fontSize: 24,
                                    fontWeight: FontWeight.bold,
                                    letterSpacing: 4,
                                    color: Color(0xFF1A1B35),
                                  ),
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.copy),
                                onPressed: () {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('OTP copied!'),
                                      duration: Duration(seconds: 1),
                                    ),
                                  );
                                },
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                  // Main tracking card
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 20,
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Status indicator
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: color.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                width: 8,
                                height: 8,
                                decoration: BoxDecoration(
                                  color: color,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'On the way',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: color,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Driver details
                        Row(
                          children: [
                            Container(
                              width: 60,
                              height: 60,
                              decoration: BoxDecoration(
                                color: color.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Center(
                                child: Text(emoji, style: const TextStyle(fontSize: 28)),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    _ride.driverName ?? 'Unknown',
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
                                        '${_ride.driverRating?.toStringAsFixed(1) ?? "N/A"} (${_ride.driverReviews})',
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
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 6,
                              ),
                              decoration: BoxDecoration(
                                color: color.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                _ride.vehiclePlate ?? 'N/A',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: color,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 20),
                        const Divider(),
                        const SizedBox(height: 16),

                        // Action buttons
                        Row(
                          children: [
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: () {},
                                icon: const Icon(Icons.phone),
                                label: const Text('Call'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: color.withOpacity(0.1),
                                  foregroundColor: color,
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: () {},
                                icon: const Icon(Icons.message),
                                label: const Text('Chat'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: color.withOpacity(0.1),
                                  foregroundColor: color,
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: () {},
                                icon: const Icon(Icons.share),
                                label: const Text('Share'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: color.withOpacity(0.1),
                                  foregroundColor: color,
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
