import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../models/ride.dart';
import 'ride_available_screen.dart';

class RideSearchScreen extends StatefulWidget {
  const RideSearchScreen({super.key});

  @override
  State<RideSearchScreen> createState() => _RideSearchScreenState();
}

class _RideSearchScreenState extends State<RideSearchScreen> {
  final _sourceController = TextEditingController();
  final _destinationController = TextEditingController();
  final _api = ApiService();
  late final AuthService _authService;
  
  String _selectedVehicle = 'car'; // 'bike', 'auto', 'car', 'premium'
  bool _isSearching = false;
  String? _error;
  List<Map<String, dynamic>> _sourceStops = [];
  List<Map<String, dynamic>> _destinationStops = [];
  bool _showSourceSuggestions = false;
  bool _showDestinationSuggestions = false;
  String _selectedCarType = 'sedan'; // For car options

  final List<Map<String, String>> _vehicleTypes = [
    {'type': 'bike', 'label': '🏍️ Bike', 'description': 'It\'s Bike'},
    {'type': 'auto', 'label': '🚕 Auto', 'description': 'Budget ride'},
    {'type': 'car', 'label': '🚗 Car', 'description': 'Select type'},
    {'type': 'premium', 'label': '🚙 Premium', 'description': 'Luxury'},
  ];

  final List<Map<String, String>> _carTypes = [
    {'type': 'sedan', 'label': 'Sedan', 'emoji': '🚗'},
    {'type': 'suv', 'label': 'SUV', 'emoji': '🚙'},
    {'type': 'uberxl', 'label': 'UberXL', 'emoji': '🚐'},
  ];

  @override
  void initState() {
    super.initState();
    _authService = AuthService(_api);
  }

  @override
  void dispose() {
    _sourceController.dispose();
    _destinationController.dispose();
    super.dispose();
  }

  Future<void> _searchStops(String query, bool isSource) async {
    if (query.isEmpty) {
      setState(() {
        if (isSource) {
          _sourceStops = [];
          _showSourceSuggestions = false;
        } else {
          _destinationStops = [];
          _showDestinationSuggestions = false;
        }
      });
      return;
    }

    try {
      final stops = await _api.searchStops(query);
      setState(() {
        if (isSource) {
          _sourceStops = stops;
          _showSourceSuggestions = true;
        } else {
          _destinationStops = stops;
          _showDestinationSuggestions = true;
        }
      });
    } catch (e) {
      print('Error searching stops: $e');
    }
  }

  Future<void> _searchRides() async {
    final source = _sourceController.text.trim();
    final destination = _destinationController.text.trim();

    if (source.isEmpty || destination.isEmpty) {
      setState(() => _error = 'Please enter both source and destination');
      return;
    }

    setState(() {
      _isSearching = true;
      _error = null;
    });

    try {
      // Ensure auth is loaded
      await _authService.ensureAuthLoaded();

      // Call backend to search rides
      // For now, we'll create mock rides for demo
      final mockRides = _generateMockRides(source, destination);

      if (!mounted) return;

      // Navigate to available rides screen
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => RideAvailableScreen(
            source: source,
            destination: destination,
            vehicleType: _selectedVehicle,
            rides: mockRides,
          ),
        ),
      );
    } catch (e) {
      setState(() => _error = 'Failed to search rides: $e');
    } finally {
      if (mounted) {
        setState(() => _isSearching = false);
      }
    }
  }

  List<Ride> _generateMockRides(String source, String destination) {
    final now = DateTime.now();
    return [
      Ride(
        id: 1,
        source: source,
        destination: destination,
        driverName: 'Rajesh Kumar',
        driverPhone: '+919876543210',
        driverRating: 4.8,
        driverReviews: 234,
        vehicleType: 'car',
        vehiclePlate: 'MH02AB1234',
        fare: 250.0,
        estimatedMinutes: 8,
        status: 'available',
        createdAt: now,
      ),
      Ride(
        id: 2,
        source: source,
        destination: destination,
        driverName: 'Priya Singh',
        driverPhone: '+919876543211',
        driverRating: 4.9,
        driverReviews: 456,
        vehicleType: 'car',
        vehiclePlate: 'MH02CD5678',
        fare: 280.0,
        estimatedMinutes: 5,
        status: 'available',
        createdAt: now,
      ),
      Ride(
        id: 3,
        source: source,
        destination: destination,
        driverName: 'Amit Patel',
        driverPhone: '+919876543212',
        driverRating: 4.7,
        driverReviews: 189,
        vehicleType: 'auto',
        vehiclePlate: 'MH02EF9012',
        fare: 180.0,
        estimatedMinutes: 10,
        status: 'available',
        createdAt: now,
      ),
      Ride(
        id: 4,
        source: source,
        destination: destination,
        driverName: 'Deepak Verma',
        driverPhone: '+919876543213',
        driverRating: 4.6,
        driverReviews: 312,
        vehicleType: 'premium',
        vehiclePlate: 'MH02GH3456',
        fare: 380.0,
        estimatedMinutes: 7,
        status: 'available',
        createdAt: now,
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        title: const Text(
          'Book a Ride',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: Color(0xFF1A1B35),
            letterSpacing: 0.3,
          ),
        ),
        backgroundColor: Colors.white,
        elevation: 1,
        shadowColor: Colors.black.withOpacity(0.08),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Color(0xFF1A1B35)),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header info
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF5974FF).withOpacity(0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF5974FF).withOpacity(0.15), width: 1),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, color: Color(0xFF5974FF), size: 20),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Enter your route details below to find available rides',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[700],
                          fontWeight: FontWeight.w500,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // From/To Section
              _buildLocationCard(
                label: 'Pickup Location',
                controller: _sourceController,
                hint: 'Select your starting point',
                icon: Icons.location_on,
                iconColor: Colors.green,
                onChanged: (value) => _searchStops(value, true),
                suggestions: _sourceStops,
                showSuggestions: _showSourceSuggestions,
                onSelectSuggestion: (stop) {
                  setState(() {
                    _sourceController.text = stop['name'] ?? '';
                    _showSourceSuggestions = false;
                  });
                },
              ),
              const SizedBox(height: 12),
              
              // Swap button
              Center(
                child: Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(color: const Color(0xFFE8EAEE), width: 1.5),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.06),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.swap_vert, color: Color(0xFF5974FF), size: 20),
                    onPressed: () {
                      final temp = _sourceController.text;
                      _sourceController.text = _destinationController.text;
                      _destinationController.text = temp;
                    },
                  ),
                ),
              ),
              const SizedBox(height: 12),

              _buildLocationCard(
                label: 'Dropoff Location',
                controller: _destinationController,
                hint: 'Where would you like to go?',
                icon: Icons.location_on,
                iconColor: Colors.red,
                onChanged: (value) => _searchStops(value, false),
                suggestions: _destinationStops,
                showSuggestions: _showDestinationSuggestions,
                onSelectSuggestion: (stop) {
                  setState(() {
                    _destinationController.text = stop['name'] ?? '';
                    _showDestinationSuggestions = false;
                  });
                },
              ),
              const SizedBox(height: 28),

              // Vehicle Type Selection - Compact
              const Text(
                'Ride Type',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF1A1B35),
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 10),
              SizedBox(
                height: 70,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: _vehicleTypes.length,
                  itemBuilder: (context, index) {
                    final vehicle = _vehicleTypes[index];
                    final isSelected = vehicle['type'] == _selectedVehicle;
                    return Padding(
                      padding: EdgeInsets.only(right: index < _vehicleTypes.length - 1 ? 10 : 0),
                      child: GestureDetector(
                        onTap: () => setState(() => _selectedVehicle = vehicle['type']!),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                          decoration: BoxDecoration(
                            color: isSelected ? const Color(0xFF5974FF) : Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: isSelected ? const Color(0xFF5974FF) : const Color(0xFFE8EAEE),
                              width: 1.5,
                            ),
                            boxShadow: isSelected
                                ? [
                                    BoxShadow(
                                      color: const Color(0xFF5974FF).withOpacity(0.2),
                                      blurRadius: 8,
                                      offset: const Offset(0, 2),
                                    ),
                                  ]
                                : [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.03),
                                      blurRadius: 4,
                                      offset: const Offset(0, 1),
                                    ),
                                  ],
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                vehicle['label']!.split(' ')[0],
                                style: TextStyle(
                                  fontSize: 20,
                                  color: isSelected ? Colors.white : Colors.black87,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                vehicle['description']!,
                                style: TextStyle(
                                  fontSize: 10,
                                  color: isSelected ? Colors.white70 : const Color(0xFF8C90A3),
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),

              // Car Type Options - Show only when Car is selected
              if (_selectedVehicle == 'car') ...[
                const SizedBox(height: 14),
                const Text(
                  'Car Type',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF1A1B35),
                    letterSpacing: 0.3,
                  ),
                ),
                const SizedBox(height: 8),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: _carTypes.map((carType) {
                      final isSelected = carType['type'] == _selectedCarType;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: GestureDetector(
                          onTap: () => setState(() => _selectedCarType = carType['type']!),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                            decoration: BoxDecoration(
                              color: isSelected ? const Color(0xFFE8F0FF) : Colors.white,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                color: isSelected ? const Color(0xFF5974FF) : const Color(0xFFE8EAEE),
                                width: 1.5,
                              ),
                              boxShadow: isSelected
                                  ? [
                                      BoxShadow(
                                        color: const Color(0xFF5974FF).withOpacity(0.15),
                                        blurRadius: 6,
                                        offset: const Offset(0, 2),
                                      ),
                                    ]
                                  : [
                                      BoxShadow(
                                        color: Colors.black.withOpacity(0.02),
                                        blurRadius: 2,
                                        offset: const Offset(0, 1),
                                      ),
                                    ],
                            ),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  carType['emoji']!,
                                  style: const TextStyle(fontSize: 16),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  carType['label']!,
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w600,
                                    color: isSelected ? const Color(0xFF5974FF) : const Color(0xFF1A1B35),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ],

              const SizedBox(height: 24),

              // Error message
              if (_error != null) ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFE5E5),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFFF6B6B).withOpacity(0.3), width: 1),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: Color(0xFFFF4444), size: 18),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          _error!,
                          style: const TextStyle(
                            color: Color(0xFFFF4444),
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            height: 1.3,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
              ],

              // Search Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isSearching ? null : _searchRides,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF5974FF),
                    disabledBackgroundColor: Colors.grey[300],
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    elevation: _isSearching ? 0 : 2,
                    shadowColor: const Color(0xFF5974FF).withOpacity(0.3),
                  ),
                  child: Text(
                    _isSearching ? 'Searching Available Rides...' : 'Search Rides',
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                      letterSpacing: 0.3,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              
              // Info footer
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey[50],
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.grey[200]!, width: 1),
                ),
                child: Row(
                  children: [
                    Icon(Icons.shield, size: 16, color: Colors.grey[600]),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Your trip details are secure and encrypted',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLocationCard({
    required String label,
    required TextEditingController controller,
    required String hint,
    required IconData icon,
    required Color iconColor,
    required Function(String) onChanged,
    required List<Map<String, dynamic>> suggestions,
    required bool showSuggestions,
    required Function(Map<String, dynamic>) onSelectSuggestion,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: Color(0xFF1A1B35),
            letterSpacing: 0.3,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          onChanged: onChanged,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(color: Colors.grey[500], fontSize: 13),
            filled: true,
            fillColor: Colors.white,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            prefixIcon: Padding(
              padding: const EdgeInsets.only(left: 12, right: 12),
              child: Icon(icon, color: iconColor, size: 18),
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: Color(0xFFE8EAEE), width: 1),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: Color(0xFFE8EAEE), width: 1),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: Color(0xFF5974FF), width: 1.5),
            ),
            suffixIcon: controller.text.isNotEmpty
                ? IconButton(
                    icon: const Icon(Icons.clear, size: 18),
                    onPressed: () {
                      controller.clear();
                      onChanged('');
                    },
                  )
                : null,
          ),
        ),
        if (showSuggestions && suggestions.isNotEmpty) ...[
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.08),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                )
              ],
            ),
            child: ListView.separated(
              shrinkWrap: true,
              itemCount: suggestions.length,
              separatorBuilder: (_, __) => Divider(height: 1, color: Colors.grey[100]),
              itemBuilder: (context, index) {
                final stop = suggestions[index];
                return ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  leading: Icon(Icons.location_on_outlined, size: 18, color: Colors.grey[600]),
                  title: Text(
                    stop['name'] ?? '',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                  ),
                  subtitle: Text(
                    stop['location'] ?? '',
                    style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                  ),
                  onTap: () => onSelectSuggestion(stop),
                );
              },
            ),
          ),
        ],
      ],
    );
  }
}
