import 'package:flutter/material.dart';
import '../models/ride.dart';
import 'ride_tracking_screen.dart';

class RideBookingScreen extends StatefulWidget {
  final Ride ride;

  const RideBookingScreen({super.key, required this.ride});

  @override
  State<RideBookingScreen> createState() => _RideBookingScreenState();
}

class _RideBookingScreenState extends State<RideBookingScreen> {
  bool _isConfirming = false;
  bool _agreeToTerms = false;

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

  Future<void> _confirmBooking() async {
    if (!_agreeToTerms) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please agree to terms and conditions'),
          backgroundColor: Color(0xFFFF4444),
        ),
      );
      return;
    }

    setState(() => _isConfirming = true);

    try {
      // Simulate API call
      await Future.delayed(const Duration(seconds: 2));

      // Create confirmed ride with OTP
      final confirmedRide = Ride(
        id: widget.ride.id,
        source: widget.ride.source,
        destination: widget.ride.destination,
        driverName: widget.ride.driverName,
        driverPhone: widget.ride.driverPhone,
        driverImage: widget.ride.driverImage,
        driverRating: widget.ride.driverRating,
        driverReviews: widget.ride.driverReviews,
        vehicleType: widget.ride.vehicleType,
        vehiclePlate: widget.ride.vehiclePlate,
        fare: widget.ride.fare,
        estimatedMinutes: widget.ride.estimatedMinutes,
        status: 'confirmed',
        createdAt: widget.ride.createdAt,
        confirmedAt: DateTime.now(),
        otp: '${(DateTime.now().millisecond % 1000).toString().padLeft(3, '0')}${(DateTime.now().second).toString().padLeft(2, '0')}',
      );

      if (!mounted) return;

      // Navigate to tracking screen
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (context) => RideTrackingScreen(ride: confirmedRide),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to confirm booking: $e'),
          backgroundColor: const Color(0xFFFF4444),
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isConfirming = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getVehicleColor(widget.ride.vehicleType);
    final emoji = _getVehicleEmoji(widget.ride.vehicleType);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FE),
      appBar: AppBar(
        title: const Text('Confirm Booking'),
        backgroundColor: Colors.white,
        elevation: 0,
        leading: !_isConfirming
            ? IconButton(
                icon: const Icon(Icons.arrow_back, color: Colors.black),
                onPressed: () => Navigator.pop(context),
              )
            : null,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Driver card
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 10,
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    // Driver avatar and name
                    Row(
                      children: [
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: color.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Center(
                            child: Text(emoji, style: const TextStyle(fontSize: 40)),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                widget.ride.driverName ?? 'Unknown',
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFF1A1B35),
                                ),
                              ),
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  const Icon(Icons.star, size: 14, color: Color(0xFFFFA500)),
                                  const SizedBox(width: 4),
                                  Text(
                                    '${widget.ride.driverRating?.toStringAsFixed(1) ?? "N/A"} (${widget.ride.driverReviews})',
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
                      ],
                    ),
                    const SizedBox(height: 20),
                    const Divider(),
                    const SizedBox(height: 20),

                    // Vehicle info
                    Row(
                      children: [
                        Expanded(
                          child: _buildInfoTile('Vehicle', widget.ride.vehicleType.toUpperCase()),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildInfoTile('Plate', widget.ride.vehiclePlate ?? 'N/A'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Route details
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 10,
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    _buildRouteStep(
                      icon: Icons.location_on,
                      title: 'Pickup',
                      location: widget.ride.source,
                      color: Colors.green,
                    ),
                    const SizedBox(height: 20),
                    Container(
                      height: 40,
                      width: 2,
                      color: Colors.grey[300],
                      margin: const EdgeInsets.only(left: 20),
                    ),
                    const SizedBox(height: 20),
                    _buildRouteStep(
                      icon: Icons.location_on,
                      title: 'Dropoff',
                      location: widget.ride.destination,
                      color: Colors.red,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Price breakdown
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 10,
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    _buildPriceRow('Ride fare', '₹${widget.ride.fare.toStringAsFixed(0)}'),
                    const SizedBox(height: 8),
                    _buildPriceRow('Taxes & fees', '₹30'),
                    const SizedBox(height: 12),
                    const Divider(),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Total',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1A1B35),
                          ),
                        ),
                        Text(
                          '₹${(widget.ride.fare + 30).toStringAsFixed(0)}',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF5974FF),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Terms checkbox
              Row(
                children: [
                  Checkbox(
                    value: _agreeToTerms,
                    onChanged: (value) {
                      setState(() => _agreeToTerms = value ?? false);
                    },
                    activeColor: const Color(0xFF5974FF),
                  ),
                  Expanded(
                    child: GestureDetector(
                      onTap: () {
                        setState(() => _agreeToTerms = !_agreeToTerms);
                      },
                      child: Text(
                        'I agree to the terms and cancellation policy',
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey[700],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Confirm button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isConfirming ? null : _confirmBooking,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF5974FF),
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: Text(
                    _isConfirming ? 'Confirming...' : 'Confirm Booking',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // Cancel button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isConfirming ? null : () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: const Color(0xFF1A1B35),
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                      side: const BorderSide(color: Color(0xFFE8EAEE)),
                    ),
                  ),
                  child: const Text(
                    'Cancel',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoTile(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1A1B35),
          ),
        ),
      ],
    );
  }

  Widget _buildRouteStep({
    required IconData icon,
    required String title,
    required String location,
    required Color color,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: color.withOpacity(0.2),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: color, size: 20),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                location,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1A1B35),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildPriceRow(String label, String amount) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 14,
            color: Colors.grey[700],
          ),
        ),
        Text(
          amount,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: Color(0xFF1A1B35),
          ),
        ),
      ],
    );
  }
}
