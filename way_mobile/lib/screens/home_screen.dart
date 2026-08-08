import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import 'map_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  late final AuthService _authService;
  late Future<User> _userFuture;

  @override
  void initState() {
    super.initState();
    _authService = AuthService(_apiService);
    _userFuture = _authService.getCurrentUser();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FE),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              _buildHeader(),
              _buildMapSearchArea(context),
              const SizedBox(height: 24),
              _buildChatCategory(),
              const SizedBox(height: 24),
              _buildTravelSavings(),
              const SizedBox(height: 24),
              _buildRecommendations(),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return FutureBuilder<User>(
      future: _userFuture,
      builder: (context, snapshot) {
        String greetingName = '';
        if (snapshot.hasData && snapshot.data != null) {
          final user = snapshot.data!;
          if (user.name != null && user.name!.trim().isNotEmpty) {
            greetingName = user.name!.trim();
          } else if (user.email != null && user.email!.trim().isNotEmpty) {
            greetingName = user.email!.trim();
          } else if (user.phone != null && user.phone!.trim().isNotEmpty) {
            greetingName = user.phone!.trim();
          }
        }

        final greetingText = greetingName.isNotEmpty ? 'Hello $greetingName!' : 'Hello!';

        return Padding(
          padding: const EdgeInsets.all(20.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Text('👋', style: TextStyle(fontSize: 24)),
                  const SizedBox(width: 8),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        greetingText,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1A1B35),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              Row(
                children: [
                  _buildIconBtn('📅'),
                  const SizedBox(width: 12),
                  _buildIconBtn('🔔'),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildIconBtn(String emoji) {
    return Container(
      width: 44,
      height: 44,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Center(
        child: Text(emoji, style: const TextStyle(fontSize: 20)),
      ),
    );
  }

  Widget _buildMapSearchArea(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Container(
            // Increased height for a larger map preview
            height: 600,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.1),
              blurRadius: 20,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Stack(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: FlutterMap(
                options: MapOptions(
                  initialCenter: const LatLng(19.0760, 72.8777), // Mumbai
                  initialZoom: 13,
                ),
                children: [
                  TileLayer(
                    urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    userAgentPackageName: 'com.example.way_mobile',
                  ),
                ],
              ),
            ),
            Positioned(
              top: 16,
              right: 16,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.9),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  '32°C ☀️',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF1A1B35),
                  ),
                ),
              ),
            ),
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: GestureDetector(
                onTap: () {
                    // Navigate to full map screen
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const MapScreen()),
                    );
                  },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.1),
                        blurRadius: 10,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Row(
                    children: const [
                      Text('🔍', style: TextStyle(fontSize: 20)),
                      SizedBox(width: 12),
                      Text(
                        'Where to?',
                        style: TextStyle(
                          fontSize: 16,
                          color: Color(0xFF8C90A3),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChatCategory() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text('✨', style: TextStyle(fontSize: 24)),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Ai lorem lorem',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF1A1B35),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "19'Mar'26 | 11:36",
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Text(
                  'Chat Category',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF8C90A3),
                  ),
                ),
                const SizedBox(width: 8),
                const Text('⌄', style: TextStyle(fontSize: 12)),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildChatCard(
                    'Suggested Chat',
                    'Aesthetic Cafés Near You ↗',
                    const Color(0xFFEBF0FF),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildChatCard(
                    'Continue Planning',
                    'Get Away Weekend Trip ↗',
                    const Color(0xFFF4F6FB),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChatCard(String label, String title, Color bgColor) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: Color(0xFF8C90A3),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            title,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1A1B35),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTravelSavings() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Travel Savings',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1A1B35),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF4F6FB),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Text(
                        'May, 2026',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF1A1B35),
                        ),
                      ),
                      const SizedBox(width: 4),
                      const Text('⌄', style: TextStyle(fontSize: 10)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                const Text(
                  '₹45',
                  style: TextStyle(
                    fontSize: 36,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1A1B35),
                  ),
                ),
                const SizedBox(width: 8),
                const Text(
                  'Saved',
                  style: TextStyle(
                    fontSize: 14,
                    color: Color(0xFF8C90A3),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Column(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: const LinearProgressIndicator(
                    value: 0.6,
                    backgroundColor: Color(0xFFF4F6FB),
                    valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF5974FF)),
                    minHeight: 8,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text(
                      'Trips',
                      style: TextStyle(
                        fontSize: 12,
                        color: Color(0xFF8C90A3),
                      ),
                    ),
                    Text(
                      'Reward',
                      style: TextStyle(
                        fontSize: 12,
                        color: Color(0xFF8C90A3),
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {},
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFF4F6FB),
                  foregroundColor: const Color(0xFF1A1B35),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: const Text(
                  'Check Travel History ↗',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendations() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFFF4F6FB),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Text('🔍', style: TextStyle(fontSize: 18)),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Text(
                      'Recommendations For You....',
                      style: TextStyle(
                        fontSize: 14,
                        color: Color(0xFF8C90A3),
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.all(8),
                    child: const Text('⚙️', style: TextStyle(fontSize: 18)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildTag('For You', true),
                const SizedBox(width: 8),
                _buildTag('Trending', false),
                const SizedBox(width: 8),
                _buildTag('Live Events', false),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF4F6FB),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Event Name',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1A1B35),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '14 May, 2026 | 4.2 ★',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {},
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF5974FF),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      child: const Text(
                        'Swipe to Book Trip >>',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
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

  Widget _buildTag(String label, bool isActive) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: isActive ? const Color(0xFF5974FF) : const Color(0xFFF4F6FB),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: isActive ? Colors.white : const Color(0xFF8C90A3),
        ),
      ),
    );
  }
}
