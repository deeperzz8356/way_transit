/// Models for Travel History (UserTrip, UserTripLeg) and Statistics.
library;

// ─── UserTripLeg ───────────────────────────

class UserTripLeg {
  final int id;
  final int tripId;
  final int sequence;
  final String transportMode;
  final String origin;
  final String destination;
  final double? originLat;
  final double? originLon;
  final double? destinationLat;
  final double? destinationLon;
  final double? distanceKm;
  final int? durationMinutes;
  final double? fare;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final String? routeName;
  final String? operatorName;
  final String? ticketReference;
  final DateTime? createdAt;

  const UserTripLeg({
    required this.id,
    required this.tripId,
    required this.sequence,
    required this.transportMode,
    required this.origin,
    required this.destination,
    this.originLat,
    this.originLon,
    this.destinationLat,
    this.destinationLon,
    this.distanceKm,
    this.durationMinutes,
    this.fare,
    this.startedAt,
    this.completedAt,
    this.routeName,
    this.operatorName,
    this.ticketReference,
    this.createdAt,
  });

  factory UserTripLeg.fromJson(Map<String, dynamic> json) {
    return UserTripLeg(
      id: json['id'] as int,
      tripId: json['trip_id'] as int,
      sequence: json['sequence'] as int? ?? 1,
      transportMode: json['transport_mode'] as String? ?? 'other',
      origin: json['origin'] as String? ?? '',
      destination: json['destination'] as String? ?? '',
      originLat: (json['origin_lat'] as num?)?.toDouble(),
      originLon: (json['origin_lon'] as num?)?.toDouble(),
      destinationLat: (json['destination_lat'] as num?)?.toDouble(),
      destinationLon: (json['destination_lon'] as num?)?.toDouble(),
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
      durationMinutes: json['duration_minutes'] as int?,
      fare: (json['fare'] as num?)?.toDouble(),
      startedAt: json['started_at'] != null
          ? DateTime.tryParse(json['started_at'].toString())
          : null,
      completedAt: json['completed_at'] != null
          ? DateTime.tryParse(json['completed_at'].toString())
          : null,
      routeName: json['route_name'] as String?,
      operatorName: json['operator_name'] as String?,
      ticketReference: json['ticket_reference'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())
          : null,
    );
  }
}

// ─── UserTrip ──────────────────────────────

class UserTrip {
  final int id;
  final int userId;
  final int? bookingId;
  final String origin;
  final String destination;
  final double? originLat;
  final double? originLon;
  final double? destinationLat;
  final double? destinationLon;
  final String? transportMode;
  final double? totalDistanceKm;
  final int? totalDurationMinutes;
  final double? totalFare;
  final String? currency;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final String? routeName;
  final String? operatorName;
  final String? ticketReference;
  final int? numTransfers;
  final String status;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final List<UserTripLeg> legs;

  const UserTrip({
    required this.id,
    required this.userId,
    this.bookingId,
    required this.origin,
    required this.destination,
    this.originLat,
    this.originLon,
    this.destinationLat,
    this.destinationLon,
    this.transportMode,
    this.totalDistanceKm,
    this.totalDurationMinutes,
    this.totalFare,
    this.currency,
    this.startedAt,
    this.completedAt,
    this.routeName,
    this.operatorName,
    this.ticketReference,
    this.numTransfers,
    required this.status,
    this.createdAt,
    this.updatedAt,
    this.legs = const [],
  });

  factory UserTrip.fromJson(Map<String, dynamic> json) {
    final legsList = (json['legs'] as List<dynamic>? ?? [])
        .map((e) => UserTripLeg.fromJson(e as Map<String, dynamic>))
        .toList();

    return UserTrip(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      bookingId: json['booking_id'] as int?,
      origin: json['origin'] as String? ?? '',
      destination: json['destination'] as String? ?? '',
      originLat: (json['origin_lat'] as num?)?.toDouble(),
      originLon: (json['origin_lon'] as num?)?.toDouble(),
      destinationLat: (json['destination_lat'] as num?)?.toDouble(),
      destinationLon: (json['destination_lon'] as num?)?.toDouble(),
      transportMode: json['transport_mode'] as String?,
      totalDistanceKm: (json['total_distance_km'] as num?)?.toDouble(),
      totalDurationMinutes: json['total_duration_minutes'] as int?,
      totalFare: (json['total_fare'] as num?)?.toDouble(),
      currency: json['currency'] as String? ?? 'INR',
      startedAt: json['started_at'] != null
          ? DateTime.tryParse(json['started_at'].toString())
          : null,
      completedAt: json['completed_at'] != null
          ? DateTime.tryParse(json['completed_at'].toString())
          : null,
      routeName: json['route_name'] as String?,
      operatorName: json['operator_name'] as String?,
      ticketReference: json['ticket_reference'] as String?,
      numTransfers: json['num_transfers'] as int?,
      status: json['status'] as String? ?? 'completed',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'].toString())
          : null,
      legs: legsList,
    );
  }

  /// Dominant mode display string
  String get modeLabel {
    switch ((transportMode ?? 'other').toLowerCase()) {
      case 'walking': return 'Walking';
      case 'bus': return 'Bus';
      case 'train':
      case 'rail': return 'Train';
      case 'metro': return 'Metro';
      case 'auto': return 'Auto';
      case 'cab': return 'Cab';
      case 'bike': return 'Bike';
      case 'car': return 'Car';
      default: return 'Other';
    }
  }

  String get modeEmoji {
    switch ((transportMode ?? 'other').toLowerCase()) {
      case 'walking': return '🚶';
      case 'bus': return '🚌';
      case 'train':
      case 'rail': return '🚆';
      case 'metro': return '🚇';
      case 'auto': return '🛺';
      case 'cab': return '🚕';
      case 'bike': return '🚲';
      case 'car': return '🚗';
      default: return '🚍';
    }
  }

  String get formattedFare {
    if (totalFare == null || totalFare == 0) return 'Free';
    final sym = currency == 'INR' ? '₹' : (currency ?? '');
    return '$sym${totalFare!.toStringAsFixed(0)}';
  }

  String get formattedDuration {
    final mins = totalDurationMinutes ?? 0;
    if (mins == 0) return '—';
    if (mins < 60) return '${mins}m';
    final h = mins ~/ 60;
    final m = mins % 60;
    return m > 0 ? '${h}h ${m}m' : '${h}h';
  }

  String get formattedDistance {
    if (totalDistanceKm == null || totalDistanceKm == 0) return '—';
    return '${totalDistanceKm!.toStringAsFixed(1)} km';
  }

  bool get isCompleted => status == 'completed';
  bool get isCancelled => status == 'cancelled';
}

// ─── Statistics ────────────────────────────

class TransportModeStats {
  final String transportMode;
  final int tripCount;
  final double totalDistanceKm;
  final int totalDurationMinutes;
  final double totalFare;

  const TransportModeStats({
    required this.transportMode,
    required this.tripCount,
    required this.totalDistanceKm,
    required this.totalDurationMinutes,
    required this.totalFare,
  });

  factory TransportModeStats.fromJson(Map<String, dynamic> json) {
    return TransportModeStats(
      transportMode: json['transport_mode'] as String? ?? 'other',
      tripCount: json['trip_count'] as int? ?? 0,
      totalDistanceKm: (json['total_distance_km'] as num?)?.toDouble() ?? 0.0,
      totalDurationMinutes: json['total_duration_minutes'] as int? ?? 0,
      totalFare: (json['total_fare'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class WeeklyStats {
  final String weekStart;
  final int tripCount;
  final double totalDistanceKm;
  final double totalFare;

  const WeeklyStats({
    required this.weekStart,
    required this.tripCount,
    required this.totalDistanceKm,
    required this.totalFare,
  });

  factory WeeklyStats.fromJson(Map<String, dynamic> json) {
    return WeeklyStats(
      weekStart: json['week_start'] as String? ?? '',
      tripCount: json['trip_count'] as int? ?? 0,
      totalDistanceKm: (json['total_distance_km'] as num?)?.toDouble() ?? 0.0,
      totalFare: (json['total_fare'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class MonthlyStats {
  final String month;
  final int tripCount;
  final double totalDistanceKm;
  final double totalFare;

  const MonthlyStats({
    required this.month,
    required this.tripCount,
    required this.totalDistanceKm,
    required this.totalFare,
  });

  factory MonthlyStats.fromJson(Map<String, dynamic> json) {
    return MonthlyStats(
      month: json['month'] as String? ?? '',
      tripCount: json['trip_count'] as int? ?? 0,
      totalDistanceKm: (json['total_distance_km'] as num?)?.toDouble() ?? 0.0,
      totalFare: (json['total_fare'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class GreenTravelStats {
  final double totalCo2Kg;
  final double co2SavedVsCarKg;
  final double publicTransportDistanceKm;
  final double walkingDistanceKm;
  final String? greenestMode;
  final String note;

  const GreenTravelStats({
    required this.totalCo2Kg,
    required this.co2SavedVsCarKg,
    required this.publicTransportDistanceKm,
    required this.walkingDistanceKm,
    this.greenestMode,
    required this.note,
  });

  factory GreenTravelStats.fromJson(Map<String, dynamic> json) {
    return GreenTravelStats(
      totalCo2Kg: (json['total_co2_kg'] as num?)?.toDouble() ?? 0.0,
      co2SavedVsCarKg: (json['co2_saved_vs_car_kg'] as num?)?.toDouble() ?? 0.0,
      publicTransportDistanceKm:
          (json['public_transport_distance_km'] as num?)?.toDouble() ?? 0.0,
      walkingDistanceKm:
          (json['walking_distance_km'] as num?)?.toDouble() ?? 0.0,
      greenestMode: json['greenest_mode'] as String?,
      note: json['note'] as String? ?? '',
    );
  }
}

class TravelStatsOverview {
  final int totalTrips;
  final double totalDistanceKm;
  final int totalDurationMinutes;
  final double totalFare;
  final double averageDistanceKm;
  final double averageDurationMinutes;
  final String? mostUsedMode;
  final List<TransportModeStats> byMode;
  final List<WeeklyStats> weekly;
  final List<MonthlyStats> monthly;
  final GreenTravelStats green;
  final String period;

  const TravelStatsOverview({
    required this.totalTrips,
    required this.totalDistanceKm,
    required this.totalDurationMinutes,
    required this.totalFare,
    required this.averageDistanceKm,
    required this.averageDurationMinutes,
    this.mostUsedMode,
    required this.byMode,
    required this.weekly,
    required this.monthly,
    required this.green,
    required this.period,
  });

  factory TravelStatsOverview.fromJson(Map<String, dynamic> json) {
    return TravelStatsOverview(
      totalTrips: json['total_trips'] as int? ?? 0,
      totalDistanceKm: (json['total_distance_km'] as num?)?.toDouble() ?? 0.0,
      totalDurationMinutes: json['total_duration_minutes'] as int? ?? 0,
      totalFare: (json['total_fare'] as num?)?.toDouble() ?? 0.0,
      averageDistanceKm: (json['average_distance_km'] as num?)?.toDouble() ?? 0.0,
      averageDurationMinutes:
          (json['average_duration_minutes'] as num?)?.toDouble() ?? 0.0,
      mostUsedMode: json['most_used_mode'] as String?,
      byMode: (json['by_mode'] as List<dynamic>? ?? [])
          .map((e) => TransportModeStats.fromJson(e as Map<String, dynamic>))
          .toList(),
      weekly: (json['weekly'] as List<dynamic>? ?? [])
          .map((e) => WeeklyStats.fromJson(e as Map<String, dynamic>))
          .toList(),
      monthly: (json['monthly'] as List<dynamic>? ?? [])
          .map((e) => MonthlyStats.fromJson(e as Map<String, dynamic>))
          .toList(),
      green: GreenTravelStats.fromJson(
          json['green'] as Map<String, dynamic>? ?? {}),
      period: json['period'] as String? ?? 'all_time',
    );
  }

  String get formattedTotalTime {
    if (totalDurationMinutes == 0) return '0m';
    final h = totalDurationMinutes ~/ 60;
    final m = totalDurationMinutes % 60;
    if (h == 0) return '${m}m';
    return m > 0 ? '${h}h ${m}m' : '${h}h';
  }

  String get formattedFare {
    return '₹${totalFare.toStringAsFixed(0)}';
  }
}
