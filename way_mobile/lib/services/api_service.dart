import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../config/api_config.dart';
import '../models/user.dart';
import '../models/route.dart';
import '../models/booking.dart';

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

  // Authentication
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.login}'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {
        'username': email,
        'password': password,
      },
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Login failed: ${response.body}');
    }
  }

  Future<User> signup(String email, String password) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.signup}'),
      headers: _headers,
      body: json.encode({
        'email': email,
        'password': password,
      }),
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
      Uri.parse('$_baseUrl${ApiConfig.searchRoutes}?source=$source&destination=$destination'),
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

  Future<List<Booking>> getMyBookings() async {
    final response = await http.get(
      Uri.parse('$_baseUrl${ApiConfig.myBookings}'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => Booking.fromJson(json)).toList();
    } else {
      throw Exception('Failed to get bookings: ${response.body}');
    }
  }

  Future<Booking> addTicket({
    required String source,
    required String destination,
    String? imageUrl,
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.addTicket}'),
      headers: _headers,
      body: json.encode({
        'source': source,
        'destination': destination,
        'image_url': imageUrl,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return Booking.fromJson(json.decode(response.body));
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
      return TicketUploadResult.fromJson(json.decode(body) as Map<String, dynamic>);
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
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl${ApiConfig.ticketJobConfirm(jobId)}'),
      headers: _headers,
      body: json.encode({
        'source': source,
        'destination': destination,
        'operator': operator,
        'travel_date': travelDate,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return Booking.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to confirm ticket: ${response.body}');
  }
}
