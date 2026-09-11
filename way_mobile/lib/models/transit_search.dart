// models/transit_search.dart
// Data models for the Source → Destination transit search feature.

/// One stop returned by GET /search/stops
class StopResult {
  final int id;
  final String stopCode;
  final String name;
  final double? lat;
  final double? lon;
  final String? mode;
  final int? operatorId;

  const StopResult({
    required this.id,
    required this.stopCode,
    required this.name,
    this.lat,
    this.lon,
    this.mode,
    this.operatorId,
  });

  factory StopResult.fromJson(Map<String, dynamic> json) {
    return StopResult(
      id: json['id'] as int,
      stopCode: (json['stop_code'] as String?) ?? '',
      name: (json['name'] as String?) ?? '',
      lat: (json['lat'] as num?)?.toDouble(),
      lon: (json['lon'] as num?)?.toDouble(),
      mode: json['mode'] as String?,
      operatorId: json['operator_id'] as int?,
    );
  }
}

/// Time + sequence info for one end of a trip result.
class TripStopInfo {
  final int stopId;
  final String stopCode;
  final String name;
  final double? lat;
  final double? lon;
  final String arrivalTime;
  final String departureTime;
  final int stopSequence;

  const TripStopInfo({
    required this.stopId,
    required this.stopCode,
    required this.name,
    this.lat,
    this.lon,
    required this.arrivalTime,
    required this.departureTime,
    required this.stopSequence,
  });

  factory TripStopInfo.fromJson(Map<String, dynamic> json) {
    return TripStopInfo(
      stopId: json['stop_id'] as int,
      stopCode: (json['stop_code'] as String?) ?? '',
      name: (json['name'] as String?) ?? '',
      lat: (json['lat'] as num?)?.toDouble(),
      lon: (json['lon'] as num?)?.toDouble(),
      // Backend sends "HH:MM:SS" or "HH:MM"; both are fine.
      arrivalTime: (json['arrival_time'] as String?) ?? '',
      departureTime: (json['departure_time'] as String?) ?? '',
      stopSequence: (json['stop_sequence'] as int?) ?? 0,
    );
  }
}

/// One matching trip returned by POST /search/trips.
class TripSearchResult {
  final int tripId;
  final String tripCode;
  final String tripName;
  final String direction;   // "DN" | "UP" | "" — backend sends Optional[str]
  final int routeId;
  final String routeCode;
  final String routeName;
  final String mode;
  final int? operatorId;
  final String? operatorName;
  final TripStopInfo source;
  final TripStopInfo destination;

  const TripSearchResult({
    required this.tripId,
    required this.tripCode,
    required this.tripName,
    required this.direction,
    required this.routeId,
    required this.routeCode,
    required this.routeName,
    required this.mode,
    this.operatorId,
    this.operatorName,
    required this.source,
    required this.destination,
  });

  factory TripSearchResult.fromJson(Map<String, dynamic> json) {
    return TripSearchResult(
      tripId: json['trip_id'] as int,
      tripCode: (json['trip_code'] as String?) ?? '',
      tripName: (json['trip_name'] as String?) ?? '',
      // FIX: direction is Optional[str] on backend — null-safe coerce to ''
      direction: (json['direction'] as String?) ?? '',
      routeId: json['route_id'] as int,
      routeCode: (json['route_code'] as String?) ?? '',
      routeName: (json['route_name'] as String?) ?? '',
      mode: (json['mode'] as String?) ?? '',
      operatorId: json['operator_id'] as int?,
      operatorName: json['operator_name'] as String?,
      source: TripStopInfo.fromJson(json['source'] as Map<String, dynamic>),
      destination:
          TripStopInfo.fromJson(json['destination'] as Map<String, dynamic>),
    );
  }

  // ── Display helpers ────────────────────────────────────────────────────

  /// Departure time at source in "08:05 AM" format.
  String get departureTimeDisplay => _fmtTime(source.departureTime);

  /// Arrival time at destination in "09:47 PM" format.
  String get arrivalTimeDisplay => _fmtTime(destination.arrivalTime);

  /// Human-readable journey duration, e.g. "47m" or "1h 12m".
  /// Handles overnight crossings (arr < dep wraps around midnight).
  String get durationDisplay {
    try {
      final dep = _toMinutes(source.departureTime);
      final arr = _toMinutes(destination.arrivalTime);
      int diff = arr - dep;
      if (diff < 0) diff += 24 * 60;
      if (diff == 0) return '';
      final h = diff ~/ 60;
      final m = diff % 60;
      if (h > 0 && m > 0) return '${h}h ${m}m';
      if (h > 0) return '${h}h';
      return '${m}m';
    } catch (_) {
      return '';
    }
  }

  /// Hex colour representing the transport mode.
  String get modeColorHex {
    switch (mode.toLowerCase()) {
      case 'train':
      case 'rail':
        return '#B45309';
      case 'metro':
      case 'subway':
        return '#7C3AED';
      case 'bus':
        return '#DC2626';
      default:
        return '#64748B';
    }
  }

  /// Best available display name: trip name > route name > "Service".
  String get displayName {
    if (tripName.isNotEmpty) return tripName;
    if (routeName.isNotEmpty) return routeName;
    return 'Service';
  }
}

// ── Private helpers ────────────────────────────────────────────────────────

/// Converts "HH:MM" or "HH:MM:SS" (including GTFS overnight times like
/// "25:30:00") to a 12-hour clock string like "08:05 AM" or "01:30 AM".
String _fmtTime(String t) {
  if (t.isEmpty) return '--:--';
  final parts = t.split(':');
  if (parts.length < 2) return t;

  // Raw hour can exceed 23 for GTFS overnight services (e.g. 25 means 1 AM
  // of the next day). We display the clock-face time, not the GTFS offset.
  final rawH = int.tryParse(parts[0]) ?? 0;
  final rawM = int.tryParse(parts[1]) ?? 0;
  final clockH = rawH % 24; // 25 → 1, 0 → 0, 13 → 13

  final isPm = clockH >= 12;
  final h12 = clockH % 12 == 0 ? 12 : clockH % 12;
  final mm = rawM.toString().padLeft(2, '0');
  return '$h12:$mm ${isPm ? 'PM' : 'AM'}';
}

/// Returns total minutes since midnight for a "HH:MM(:SS)" string.
/// Handles GTFS overnight hours (e.g. "25:30" = 1530 min past midnight).
int _toMinutes(String t) {
  final parts = t.split(':');
  final h = int.tryParse(parts[0]) ?? 0;
  final m = parts.length > 1 ? (int.tryParse(parts[1]) ?? 0) : 0;
  return h * 60 + m;
}
