import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/booking.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../nav/app_nav.dart';
import '../config/api_config.dart';
import 'map_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = ApiService();
  final _mapController = MapController();
  late final AuthService _authService;
  late Future<User> _userFuture;
  Booking? _activeTicket;
  bool _isLoading = true;
  LatLng? _fromPoint;
  LatLng? _toPoint;

  @override
  void initState() {
    super.initState();
    _authService = AuthService(_api);
    // ✅ FIX: Load token first, THEN load user data
    _userFuture = _loadUserWithToken();
    _fetchActiveTicket();
    AppNav.homeRefreshTick.addListener(_onHomeRefresh);
  }

  Future<User> _loadUserWithToken() async {
    // Ensure token is loaded on API service first
    await _authService.ensureAuthLoaded();
    return await _authService.getCurrentUser();
  }

  @override
  void dispose() {
    AppNav.homeRefreshTick.removeListener(_onHomeRefresh);
    super.dispose();
  }

  void _onHomeRefresh() {
    _fetchActiveTicket();
  }

  Future<void> _fetchActiveTicket() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');
      _api.setToken(token ?? 'dev-token');

      final bookings = await _api.getMyBookings();
      if (!mounted) return;

      Booking? active;
      for (final b in bookings) {
        if (b.status.toUpperCase() == 'IN_PROGRESS' || b.activeBadge) {
          active = b;
          break;
        }
      }

      setState(() {
        _activeTicket = active;
        _isLoading = false;
        if (active == null) {
          _fromPoint = null;
          _toPoint = null;
        }
      });

      if (active != null) {
        await _resolveMapPoints(active);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _resolveMapPoints(Booking ticket) async {
    LatLng? from;
    LatLng? to;
    try {
      if (ticket.source != null && ticket.source!.isNotEmpty) {
        final stops = await _api.searchStops(ticket.source!);
        if (stops.isNotEmpty) {
          from = LatLng(
            (stops.first['lat'] as num).toDouble(),
            (stops.first['lon'] as num).toDouble(),
          );
        }
      }
      if (ticket.destination != null && ticket.destination!.isNotEmpty) {
        final stops = await _api.searchStops(ticket.destination!);
        if (stops.isNotEmpty) {
          to = LatLng(
            (stops.first['lat'] as num).toDouble(),
            (stops.first['lon'] as num).toDouble(),
          );
        }
      }
    } catch (_) {}

    // Fallback Mumbai-ish offsets if stops missing
    from ??= const LatLng(19.2290, 72.8570); // approx Virar-ish NW
    to ??= const LatLng(18.9400, 72.8350); // Churchgate-ish

    if (!mounted) return;
    setState(() {
      _fromPoint = from;
      _toPoint = to;
    });

    try {
      final bounds = LatLngBounds(from, to);
      _mapController.fitBounds(
        bounds,
        options: const FitBoundsOptions(padding: EdgeInsets.all(48)),
      );
    } catch (_) {
      _mapController.move(
        LatLng(
          (from.latitude + to.latitude) / 2,
          (from.longitude + to.longitude) / 2,
        ),
        11,
      );
    }
  }

  Color get _activeColor {
    final hex = (_activeTicket?.colorHex?.isNotEmpty == true)
        ? _activeTicket!.colorHex!
        : PlatformColors.forMode(_activeTicket?.mode);
    return Color(int.parse('FF${hex.replaceFirst('#', '')}', radix: 16));
  }

  String _fmt(DateTime? dt) {
    if (dt == null) return '—';
    final l = dt.toLocal();
    return '${l.hour.toString().padLeft(2, '0')}:${l.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FE),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _fetchActiveTicket,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: Column(
              children: [
                _buildHeader(),
                if (_isLoading)
                  const Padding(
                    padding: EdgeInsets.all(20.0),
                    child: Center(child: CircularProgressIndicator()),
                  )
                else if (_activeTicket != null) ...[
                  _buildActiveBento(),
                  const SizedBox(height: 16),
                ],
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

        final greetingText = greetingName.isNotEmpty
            ? 'Hello $greetingName!'
            : 'Hello!';

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
      child: Center(child: Text(emoji, style: const TextStyle(fontSize: 20))),
    );
  }

  Widget _buildActiveBento() {
    final t = _activeTicket!;
    final color = _activeColor;
    final source = t.source ?? 'Unknown';
    final destination = t.destination ?? 'Unknown';

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: color.withValues(alpha: 0.3),
                  blurRadius: 15,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 5,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.22),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Text(
                        'ACTIVE',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 11,
                          letterSpacing: 0.8,
                        ),
                      ),
                    ),
                    const Spacer(),
                    Text(
                      (t.modeLabel ?? t.mode ?? 'Transit').toUpperCase(),
                      style: const TextStyle(
                        color: Colors.white70,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                Text(
                  '$source → $destination',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (t.ticketNumber != null) ...[
                  const SizedBox(height: 6),
                  Text(
                    'Ticket ${t.ticketNumber}',
                    style: const TextStyle(color: Colors.white70, fontSize: 13),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _bentoTile(
                  icon: Icons.schedule,
                  label: 'Start',
                  value: _fmt(t.journeyStartedAt),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _bentoTile(
                  icon: Icons.flag,
                  label: 'Est. end',
                  value: _fmt(t.journeyEstimatedEndAt),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _bentoTile(
                  icon: Icons.confirmation_number_outlined,
                  label: 'Platform',
                  value: (t.mode ?? 'other').toUpperCase(),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _bentoTile(
                  icon: Icons.payments_outlined,
                  label: 'Fare',
                  value: t.fare != null
                      ? '₹${t.fare!.toStringAsFixed(0)}'
                      : '—',
                ),
              ),
            ],
          ),
          if (t.operatorName != null) ...[
            const SizedBox(height: 10),
            _bentoTile(
              icon: Icons.business,
              label: 'Operator',
              value: t.operatorName!,
            ),
          ],
        ],
      ),
    );
  }

  Widget _bentoTile({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(icon, size: 20, color: _activeColor),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(fontSize: 11, color: Colors.black45),
                ),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMapSearchArea(BuildContext context) {
    final center = _fromPoint != null && _toPoint != null
        ? LatLng(
            (_fromPoint!.latitude + _toPoint!.latitude) / 2,
            (_fromPoint!.longitude + _toPoint!.longitude) / 2,
          )
        : const LatLng(19.0760, 72.8777);
    final markers = <Marker>[];
    if (_fromPoint != null) {
      markers.add(
        Marker(
          point: _fromPoint!,
          width: 40,
          height: 40,
          child: const Icon(Icons.trip_origin, color: Colors.green, size: 32),
        ),
      );
    }
    if (_toPoint != null) {
      markers.add(
        Marker(
          point: _toPoint!,
          width: 40,
          height: 40,
          child: const Icon(Icons.location_on, color: Colors.red, size: 36),
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Container(
        height: 320,
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
                mapController: _mapController,
                options: MapOptions(
                  center: center,
                  zoom: _activeTicket != null ? 11.0 : 13.0,
                ),
                children: [
                  TileLayer(
                    urlTemplate:
                        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    userAgentPackageName: 'com.example.way_mobile',
                  ),
                  if (_fromPoint != null && _toPoint != null)
                    PolylineLayer(
                      polylines: [
                        Polyline(
                          points: [_fromPoint!, _toPoint!],
                          color: _activeTicket != null
                              ? _activeColor
                              : const Color(0xFF5974FF),
                          strokeWidth: 4,
                        ),
                      ],
                    ),
                  MarkerLayer(markers: markers),
                ],
              ),
            ),
            if (_activeTicket != null)
              Positioned(
                top: 12,
                left: 12,
                right: 12,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 10,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.95),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${_activeTicket!.source ?? '?'} → ${_activeTicket!.destination ?? '?'}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 13,
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
                  Navigator.of(
                    context,
                  ).push(MaterialPageRoute(builder: (_) => const MapScreen()));
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 14,
                  ),
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
                    children: [
                      const Text('🔍', style: TextStyle(fontSize: 20)),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          _activeTicket != null
                              ? 'Active trip on map'
                              : 'Where to?',
                          style: const TextStyle(
                            fontSize: 16,
                            color: Color(0xFF8C90A3),
                          ),
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
                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
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
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
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
                  style: TextStyle(fontSize: 14, color: Color(0xFF8C90A3)),
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
                    valueColor: AlwaysStoppedAnimation<Color>(
                      Color(0xFF5974FF),
                    ),
                    minHeight: 8,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text(
                      'Trips',
                      style: TextStyle(fontSize: 12, color: Color(0xFF8C90A3)),
                    ),
                    Text(
                      'Reward',
                      style: TextStyle(fontSize: 12, color: Color(0xFF8C90A3)),
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
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
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
                      style: TextStyle(fontSize: 14, color: Color(0xFF8C90A3)),
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
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
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
