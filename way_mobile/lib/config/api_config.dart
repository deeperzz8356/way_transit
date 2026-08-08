import 'package:flutter/foundation.dart';

class ApiConfig {
  /// Override at build time: `--dart-define=API_BASE_URL=http://192.168.x.x:8000`
  static String get baseUrl {
    const fromEnv = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (fromEnv.isNotEmpty) return fromEnv;

    if (kIsWeb) return 'http://localhost:8000';

    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
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

  static String get agentBaseUrl {
    const fromEnv = String.fromEnvironment('AGENT_BASE_URL', defaultValue: '');
    if (fromEnv.isNotEmpty) return fromEnv;
    if (kIsWeb) return 'http://localhost:8001';
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return 'http://10.0.2.2:8001';
      default:
        return 'http://localhost:8001';
    }
  }

  static const String login = '/user/login';
  static const String signup = '/user/signup';
  static const String getCurrentUser = '/user/me';
  static const String searchRoutes = '/search/routes';
  static const String searchStops = '/search/stops';
  static const String bookRoute = '/booking/book';
  static const String myBookings = '/booking/my-bookings';
  static const String wallet = '/booking/wallet';
  static const String addTicket = '/booking/add-ticket';
  static const String uploadTicket = '/booking/upload-ticket';
  static const String listPasses = '/booking/passes';

  static String ticketJob(int jobId) => '/booking/ticket-jobs/$jobId';
  static String ticketJobEvents(int jobId) => '/booking/ticket-jobs/$jobId/events';
  static String ticketJobConfirm(int jobId) => '/booking/ticket-jobs/$jobId/confirm';
  static String ticketDetail(int id) => '/booking/tickets/$id';
  static String deleteTicket(int id) => '/booking/tickets/$id';
  static String startJourney(int id) => '/booking/tickets/$id/start-journey';
  static String completeJourney(int id) => '/booking/tickets/$id/complete';
  static String addPass(int passId) => '/booking/passes/$passId/add';

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

class PlatformColors {
  static const rail = '#B45309';
  static const metro = '#7C3AED';
  static const bus = '#DC2626';
  static const cab = '#0D9488';
  static const other = '#64748B';

  static String forMode(String? mode) {
    switch ((mode ?? 'other').toLowerCase()) {
      case 'rail':
        return rail;
      case 'metro':
        return metro;
      case 'bus':
        return bus;
      case 'cab':
        return cab;
      default:
        return other;
    }
  }
}
