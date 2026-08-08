import 'package:flutter/foundation.dart';

class ApiConfig {
  /// Override at build time: `--dart-define=API_BASE_URL=http://192.168.x.x:8000`
  static String get baseUrl {
    const fromEnv = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (fromEnv.isNotEmpty) return fromEnv;

    // Chrome / Edge / desktop → host machine
    if (kIsWeb) return 'http://localhost:8000';

    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        // Android emulator loopback to host
        return 'http://10.0.2.2:8000';
      case TargetPlatform.iOS:
      case TargetPlatform.macOS:
      case TargetPlatform.windows:
      case TargetPlatform.linux:
        return 'http://localhost:8000';
      default:
        return 'http://localhost:8000';
    }
  }

  static const String login = '/users/login';
  static const String signup = '/users/signup';
  static const String getCurrentUser = '/users/me';
  static const String firebaseAuth = '/auth/firebase';
  static const String searchRoutes = '/search/routes';
  static const String bookRoute = '/booking/book';
  static const String myBookings = '/booking/my-bookings';
  static const String addTicket = '/booking/add-ticket';
  static const String uploadTicket = '/booking/upload-ticket';

  static String ticketJob(int jobId) => '/booking/ticket-jobs/$jobId';
  static String ticketJobEvents(int jobId) => '/booking/ticket-jobs/$jobId/events';
  static String ticketJobConfirm(int jobId) => '/booking/ticket-jobs/$jobId/confirm';

  static String resolveUrl(String pathOrUrl) {
    if (pathOrUrl.startsWith('http://') || pathOrUrl.startsWith('https://')) {
      return pathOrUrl;
    }
    if (pathOrUrl.startsWith('/')) {
      return '$baseUrl$pathOrUrl';
    }
    return '$baseUrl/$pathOrUrl';
  }
}
