import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../config/api_config.dart';
import '../models/user.dart';
import '../models/route.dart';
import '../models/booking.dart';
import '../models/ride.dart';
import '../models/user_trip.dart';

class TicketUploadResult {
  final int jobId;
  final String status;
  final String imageUrl;
  final String eventsUrl;

  TicketUploadResult({
    required this.jobId,
    required this.status,
    required this.imageUrl,
    required this.eventsUrl,
  });

  factory TicketUploadResult.fromJson(Map<String, dynamic> json) {
    return TicketUploadResult(
      jobId: json['job_id'] as int,
      status: json['status'] as String? ?? 'uploaded',
      imageUrl: json['image_url'] as String? ?? '',
      eventsUrl: json['events_url'] as String? ?? '',
    );
  }
}

class ApiService {
  final String _baseUrl;
  String? _token;

  ApiService({String? baseUrl}) : _baseUrl = baseUrl ?? ApiConfig.baseUrl;

  void setToken(String? token) {
    _token = token;
  }

  Map<String, String> get _headers {
    final headers = {'Content-Type': 'application/json'};
    if (_token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  Map<String, String> get _authHeaders {
    final headers = <String, String>{};
    if (_token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  /// Get current Firebase ID token if user is logged in
  Future<String?> getFirebaseIdToken() async {
    try {
      final user = firebase_auth.FirebaseAuth.instance.currentUser;
      if (user != null) {
        return await user.getIdToken();
      }
    } catch (_) {
      // Silently fail
    }
    return null;
  }

  // Authentication
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.login}'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'username': email, 'password': password},
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Login failed: ${response.body}');
    }
  }

  // OAuth-style login (development helper)
  Future<Map<String, dynamic>> oauthLogin({
    required String provider,
    required String email,
    String? providerId,
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/user/oauth_login'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'provider': provider,
        'email': email,
        'provider_id': providerId,
      }),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    } else {
      throw Exception('OAuth login failed: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> firebaseAuth(String idToken) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.firebaseAuth}'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'id_token': idToken}),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Firebase authentication failed: ${response.body}');
  }

  Future<User> updateCurrentUser(String name) async {
    final response = await http.put(
      Uri.parse('$_baseUrl${ApiConfig.getCurrentUser}'),
      headers: _headers,
      body: json.encode({'name': name}),
    );

    if (response.statusCode == 200) {
      return User.fromJson(json.decode(response.body));
    }
    throw Exception('Update profile failed: ${response.body}');
  }

  Future<void> deleteCurrentUser() async {
    final response = await http.delete(
      Uri.parse('$_baseUrl${ApiConfig.getCurrentUser}'),
      headers: _headers,
    );
    if (response.statusCode == 200) {
      return;
    }
    throw Exception('Delete account failed: ${response.body}');
  }

  Future<User> signup(String email, String password) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.signup}'),
      headers: _headers,
      body: json.encode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      return User.fromJson(json.decode(response.body));
    } else {
      throw Exception('Signup failed: ${response.body}');
    }
  }

  Future<User> getCurrentUser() async {
    final response = await http.get(
      Uri.parse('$_baseUrl${ApiConfig.getCurrentUser}'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return User.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to get user: ${response.body}');
    }
  }

  // Search
  Future<List<Route>> searchRoutes(String source, String destination) async {
    final response = await http.get(
      Uri.parse(
        '$_baseUrl${ApiConfig.searchRoutes}?source=$source&destination=$destination',
      ),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => Route.fromJson(json)).toList();
    } else {
      throw Exception('Failed to search routes: ${response.body}');
    }
  }

  // Booking
  Future<Booking> bookRoute(int routeId) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.bookRoute}'),
      headers: _headers,
      body: json.encode({'route_id': routeId}),
    );

    if (response.statusCode == 200) {
      return Booking.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to book route: ${response.body}');
    }
  }

  Future<List<Booking>> getMyBookings({String? mode}) async {
    final q = (mode != null && mode.isNotEmpty && mode != 'all')
        ? '?mode=$mode'
        : '';
    final response = await http.get(
      Uri.parse('$_baseUrl${ApiConfig.myBookings}$q'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => Booking.fromJson(json)).toList();
    } else {
      throw Exception('Failed to get bookings: ${response.body}');
    }
  }

  Future<WalletData> getWallet({String? mode}) async {
    final q = (mode != null && mode.isNotEmpty && mode != 'all')
        ? '?mode=$mode'
        : '';
    final response = await http.get(
      Uri.parse('$_baseUrl${ApiConfig.wallet}$q'),
      headers: _headers,
    );
    if (response.statusCode == 200) {
      return WalletData.fromJson(
        json.decode(response.body) as Map<String, dynamic>,
      );
    }
    throw Exception('Failed to get wallet: ${response.body}');
  }

  Future<Booking> addTicket({
    required String source,
    required String destination,
    String? imageUrl,
    String? ticketNumber,
    String? qrPayload,
    String? mode,
    String? operatorName,
    String? travelDate,
    String? className,
    double? fare,
    String sourceType = 'manual',
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.addTicket}'),
      headers: _headers,
      body: json.encode({
        'source': source,
        'destination': destination,
        'image_url': imageUrl,
        'ticket_number': ticketNumber,
        'qr_payload': qrPayload,
        'mode': mode,
        'operator_name': operatorName,
        'travel_date': travelDate,
        'class_name': className,
        'fare': fare,
        'source_type': sourceType,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return Booking.fromJson(json.decode(response.body));
    }
    if (response.statusCode == 409) {
      throw Exception('Already in wallet');
    }
    throw Exception('Failed to save ticket: ${response.body}');
  }

  Future<TicketUploadResult> uploadTicketImageBytes({
    required Uint8List bytes,
    required String filename,
  }) async {
    final uri = Uri.parse('$_baseUrl${ApiConfig.uploadTicket}');
    final request = http.MultipartRequest('POST', uri);
    request.headers.addAll(_authHeaders);

    final lower = filename.toLowerCase();
    final contentType = lower.endsWith('.png')
        ? 'image/png'
        : lower.endsWith('.webp')
        ? 'image/webp'
        : lower.endsWith('.gif')
        ? 'image/gif'
        : 'image/jpeg';

    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: filename,
        contentType: MediaType.parse(contentType),
      ),
    );

    final streamed = await request.send();
    final body = await streamed.stream.bytesToString();
    if (streamed.statusCode == 200 || streamed.statusCode == 201) {
      return TicketUploadResult.fromJson(
        json.decode(body) as Map<String, dynamic>,
      );
    }
    throw Exception('Upload failed (${streamed.statusCode}): $body');
  }

  Future<Map<String, dynamic>> getTicketJob(int jobId) async {
    final response = await http.get(
      Uri.parse('$_baseUrl${ApiConfig.ticketJob(jobId)}'),
      headers: _headers,
    );
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to load ticket job: ${response.body}');
  }

  /// Live-tail SSE for ticket job progress. Yields decoded event maps.
  Stream<Map<String, dynamic>> streamTicketJobEvents(int jobId) async* {
    final client = http.Client();
    try {
      final request = http.Request(
        'GET',
        Uri.parse('$_baseUrl${ApiConfig.ticketJobEvents(jobId)}'),
      );
      request.headers.addAll({
        ..._authHeaders,
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      });

      final response = await client.send(request);
      if (response.statusCode != 200) {
        final body = await response.stream.bytesToString();
        throw Exception('SSE failed (${response.statusCode}): $body');
      }

      var buffer = '';
      await for (final chunk in response.stream.transform(utf8.decoder)) {
        buffer += chunk;
        while (true) {
          final sep = buffer.indexOf('\n\n');
          if (sep < 0) break;
          final block = buffer.substring(0, sep);
          buffer = buffer.substring(sep + 2);
          for (final line in block.split('\n')) {
            if (line.startsWith('data:')) {
              final raw = line.substring(5).trim();
              if (raw.isEmpty) continue;
              try {
                final map = json.decode(raw) as Map<String, dynamic>;
                yield map;
                final event = map['event']?.toString();
                if (event == 'done' || event == 'timeout' || event == 'error') {
                  return;
                }
                if (event == 'ready' || event == 'extracted') {
                  // Keep streaming until done; ready is not terminal.
                }
              } catch (_) {
                // ignore malformed SSE payloads
              }
            }
          }
        }
      }
    } finally {
      client.close();
    }
  }

  Future<Booking> confirmTicketJob({
    required int jobId,
    required String source,
    required String destination,
    String? operator,
    String? travelDate,
    String? ticketNumber,
    String? qrPayload,
    String? mode,
    String? className,
    double? fare,
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.ticketJobConfirm(jobId)}'),
      headers: _headers,
      body: json.encode({
        'source': source,
        'destination': destination,
        'operator': operator,
        'operator_name': operator,
        'travel_date': travelDate,
        'ticket_number': ticketNumber,
        'qr_payload': qrPayload,
        'mode': mode,
        'class_name': className,
        'fare': fare,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return Booking.fromJson(json.decode(response.body));
    }
    if (response.statusCode == 409) {
      throw Exception('Already in wallet');
    }
    throw Exception('Failed to confirm ticket: ${response.body}');
  }

  Future<List<Map<String, dynamic>>> searchStops(String query, {String? mode}) async {
    final modeParam = (mode != null && mode.isNotEmpty) ? '&mode=$mode' : '';
    final response = await http.get(
      Uri.parse(
        '$_baseUrl${ApiConfig.searchStops}?q=${Uri.encodeComponent(query)}$modeParam',
      ),
      headers: _headers,
    );
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.cast<Map<String, dynamic>>();
    }
    return [];
  }

  /// POST /search/trips — returns full trip-level timetable results.
  Future<Map<String, dynamic>> searchTrips({
    required int sourceStopId,
    required int destinationStopId,
    String? mode,
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.searchTrips}'),
      headers: _headers,
      body: json.encode({
        'source_stop_id': sourceStopId,
        'destination_stop_id': destinationStopId,
        if (mode != null && mode.isNotEmpty) 'mode': mode,
      }),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    if (response.statusCode == 400 || response.statusCode == 404) {
      final body = json.decode(response.body) as Map<String, dynamic>;
      throw Exception(body['detail'] ?? 'Search error');
    }
    throw Exception('Trip search failed (${response.statusCode}): ${response.body}');
  }

  Future<Booking> getTicket(int ticketId) async {
    final response = await http.get(
      Uri.parse('$_baseUrl${ApiConfig.ticketDetail(ticketId)}'),
      headers: _headers,
    );
    if (response.statusCode == 200) {
      return Booking.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to load ticket: ${response.body}');
  }

  Future<Map<String, dynamic>> startJourney(
    int ticketId, {
    DateTime? startTime,
    DateTime? estimatedEndTime,
    bool makeActive = true,
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.startJourney(ticketId)}'),
      headers: _headers,
      body: json.encode({
        'start_time': startTime?.toUtc().toIso8601String(),
        'estimated_end_time': estimatedEndTime?.toUtc().toIso8601String(),
        'make_active': makeActive,
      }),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to start journey: ${response.body}');
  }

  Future<void> deleteTicket(int ticketId) async {
    final response = await http.delete(
      Uri.parse('$_baseUrl${ApiConfig.deleteTicket(ticketId)}'),
      headers: _headers,
    );
    if (response.statusCode == 200 || response.statusCode == 204) {
      return;
    }
    throw Exception('Failed to delete ticket: ${response.body}');
  }

  Future<Booking> completeJourney(int ticketId) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.completeJourney(ticketId)}'),
      headers: _headers,
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return Booking.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to complete journey: ${response.body}');
  }

  Future<List<UserPassItem>> listPassProducts() async {
    final response = await http.get(
      Uri.parse('$_baseUrl${ApiConfig.listPasses}'),
      headers: _headers,
    );
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data
          .map((e) => UserPassItem.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    throw Exception('Failed to list passes: ${response.body}');
  }

  Future<UserPassItem> addPassToWallet(int passId) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.addPass(passId)}'),
      headers: _headers,
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return UserPassItem.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to add pass: ${response.body}');
  }

  // ─── Ride Booking ───────────────────────────────────────────

  /// Search available rides
  Future<List<Ride>> searchRides({
    required String source,
    required String destination,
    String? vehicleType,
  }) async {
    final params = {
      'source': source,
      'destination': destination,
      if (vehicleType != null) 'vehicle_type': vehicleType,
    };
    final uri = Uri.parse(
      '$_baseUrl/rides/search',
    ).replace(queryParameters: params);
    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => Ride.fromJson(e as Map<String, dynamic>)).toList();
    }
    throw Exception('Failed to search rides: ${response.body}');
  }

  /// Book a ride
  Future<Ride> bookRide({
    required int rideId,
    required String source,
    required String destination,
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/rides/$rideId/book'),
      headers: _headers,
      body: json.encode({'source': source, 'destination': destination}),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return Ride.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to book ride: ${response.body}');
  }

  /// Get active ride
  Future<Ride> getActiveRide() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/rides/active'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return Ride.fromJson(json.decode(response.body));
    }
    throw Exception('No active ride: ${response.body}');
  }

  /// Get my rides (booking history)
  Future<List<Ride>> getMyRides({String? status}) async {
    final params = <String, String>{};
    if (status != null && status.isNotEmpty) params['status'] = status;

    final uri = Uri.parse(
      '$_baseUrl/rides/my-rides',
    ).replace(queryParameters: params);
    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => Ride.fromJson(e as Map<String, dynamic>)).toList();
    }
    throw Exception('Failed to get rides: ${response.body}');
  }

  /// Cancel a ride
  Future<void> cancelRide(int rideId) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/rides/$rideId/cancel'),
      headers: _headers,
    );

    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception('Failed to cancel ride: ${response.body}');
    }
  }

  /// Rate a completed ride
  Future<void> rateRide(int rideId, double rating, String? comment) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/rides/$rideId/rate'),
      headers: _headers,
      body: json.encode({'rating': rating, 'comment': comment}),
    );

    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception('Failed to rate ride: ${response.body}');
    }
  }

  // ─── Travel History & Statistics ────────────────────────────

  /// Get user's trips with optional filters
  Future<List<UserTrip>> getTrips({
    String? status,
    String? transportMode,
    DateTime? dateFrom,
    DateTime? dateTo,
    int limit = 100,
    int offset = 0,
  }) async {
    final params = <String, String>{
      'limit': limit.toString(),
      'offset': offset.toString(),
    };
    if (status != null && status != 'all') params['status'] = status;
    if (transportMode != null && transportMode != 'all') {
      params['transport_mode'] = transportMode;
    }
    if (dateFrom != null) params['date_from'] = dateFrom.toIso8601String();
    if (dateTo != null) params['date_to'] = dateTo.toIso8601String();

    final uri = Uri.parse('$_baseUrl/trips').replace(queryParameters: params);
    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data
          .map((e) => UserTrip.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    throw Exception('Failed to get trips: ${response.body}');
  }

  /// Get a single trip detail
  Future<UserTrip> getTrip(int tripId) async {
    final response = await http.get(
      Uri.parse('$_baseUrl/trips/$tripId'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return UserTrip.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to get trip: ${response.body}');
  }

  /// Create a manual trip (walking, manual entry, etc.)
  Future<UserTrip> createTrip({
    required String origin,
    required String destination,
    double? originLat,
    double? originLon,
    double? destinationLat,
    double? destinationLon,
    String? transportMode,
    double? totalDistanceKm,
    int? totalDurationMinutes,
    double? totalFare,
    DateTime? startedAt,
    DateTime? completedAt,
    String? routeName,
    String? operatorName,
    String? ticketReference,
    int? numTransfers,
    String status = 'completed',
    List<Map<String, dynamic>>? legs,
  }) async {
    final body = {
      'origin': origin,
      'destination': destination,
      'transport_mode': transportMode,
      'total_distance_km': totalDistanceKm,
      'total_duration_minutes': totalDurationMinutes,
      'total_fare': totalFare,
      'started_at': startedAt?.toIso8601String(),
      'completed_at': completedAt?.toIso8601String(),
      'route_name': routeName,
      'operator_name': operatorName,
      'ticket_reference': ticketReference,
      'num_transfers': numTransfers,
      'status': status,
      if (originLat != null) 'origin_lat': originLat,
      if (originLon != null) 'origin_lon': originLon,
      if (destinationLat != null) 'destination_lat': destinationLat,
      if (destinationLon != null) 'destination_lon': destinationLon,
      if (legs != null) 'legs': legs,
    };

    final response = await http.post(
      Uri.parse('$_baseUrl/trips'),
      headers: _headers,
      body: json.encode(body),
    );

    if (response.statusCode == 201 || response.statusCode == 200) {
      return UserTrip.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to create trip: ${response.body}');
  }

  /// Update a trip
  Future<UserTrip> updateTrip(
    int tripId, {
    String? origin,
    String? destination,
    String? transportMode,
    double? totalDistanceKm,
    int? totalDurationMinutes,
    double? totalFare,
    String? status,
  }) async {
    final body = <String, dynamic>{};
    if (origin != null) body['origin'] = origin;
    if (destination != null) body['destination'] = destination;
    if (transportMode != null) body['transport_mode'] = transportMode;
    if (totalDistanceKm != null) body['total_distance_km'] = totalDistanceKm;
    if (totalDurationMinutes != null) {
      body['total_duration_minutes'] = totalDurationMinutes;
    }
    if (totalFare != null) body['total_fare'] = totalFare;
    if (status != null) body['status'] = status;

    final response = await http.put(
      Uri.parse('$_baseUrl/trips/$tripId'),
      headers: _headers,
      body: json.encode(body),
    );

    if (response.statusCode == 200) {
      return UserTrip.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to update trip: ${response.body}');
  }

  /// Delete a trip
  Future<void> deleteTrip(int tripId) async {
    final response = await http.delete(
      Uri.parse('$_baseUrl/trips/$tripId'),
      headers: _headers,
    );

    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception('Failed to delete trip: ${response.body}');
    }
  }

  /// Get travel statistics
  Future<TravelStatsOverview> getTravelStats({
    String period = 'all_time',
  }) async {
    final params = {'period': period};
    final uri = Uri.parse(
      '$_baseUrl/stats/overview',
    ).replace(queryParameters: params);
    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      return TravelStatsOverview.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to get travel stats: ${response.body}');
  }
}
