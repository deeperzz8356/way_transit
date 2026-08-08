class Booking {
  final int id;
  final int userId;
  final int? routeId;
  final String status;
  final DateTime? bookedAt;
  final String? source;
  final String? destination;
  final String? imageUrl;
  final String? ticketCode;
  final String? ticketNumber;
  final String? qrPayload;
  final String? qrDisplay;
  final String? mode;
  final String? modeLabel;
  final String? colorHex;
  final String? operatorName;
  final String? className;
  final double? fare;
  final String? sourceType;
  final String? travelDate;
  final DateTime? journeyStartedAt;
  final DateTime? journeyEstimatedEndAt;
  final bool isActive;
  final double? distanceKm;
  final int? ticketTripId;

  Booking({
    required this.id,
    required this.userId,
    this.routeId,
    required this.status,
    this.bookedAt,
    this.source,
    this.destination,
    this.imageUrl,
    this.ticketCode,
    this.ticketNumber,
    this.qrPayload,
    this.qrDisplay,
    this.mode,
    this.modeLabel,
    this.colorHex,
    this.operatorName,
    this.className,
    this.fare,
    this.sourceType,
    this.travelDate,
    this.journeyStartedAt,
    this.journeyEstimatedEndAt,
    this.isActive = false,
    this.distanceKm,
    this.ticketTripId,
  });

  String get displayQr =>
      (qrDisplay != null && qrDisplay!.isNotEmpty)
          ? qrDisplay!
          : (qrPayload != null && qrPayload!.isNotEmpty)
              ? qrPayload!
              : (ticketNumber != null && ticketNumber!.isNotEmpty)
                  ? ticketNumber!
                  : (ticketCode ?? id.toString());

  bool get activeBadge =>
      isActive || status.toUpperCase() == 'IN_PROGRESS';

  factory Booking.fromJson(Map<String, dynamic> json) {
    String? source = json['source'] as String?;
    String? destination = json['destination'] as String?;
    final route = json['route'];
    if (route is Map<String, dynamic>) {
      source ??= route['source'] as String?;
      destination ??= route['destination'] as String?;
    }
    final status = json['status'] as String? ?? 'CONFIRMED';

    return Booking(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      routeId: json['route_id'] as int?,
      status: status,
      bookedAt: json['booked_at'] != null
          ? DateTime.tryParse(json['booked_at'].toString())
          : null,
      source: source,
      destination: destination,
      imageUrl: json['image_url'] as String?,
      ticketCode: json['ticket_code'] as String?,
      ticketNumber: json['ticket_number'] as String?,
      qrPayload: json['qr_payload'] as String?,
      qrDisplay: json['qr_display'] as String?,
      mode: json['mode'] as String?,
      modeLabel: json['mode_label'] as String?,
      colorHex: json['color_hex'] as String?,
      operatorName: json['operator_name'] as String?,
      className: json['class_name'] as String?,
      fare: (json['fare'] as num?)?.toDouble(),
      sourceType: json['source_type'] as String?,
      travelDate: json['travel_date']?.toString(),
      journeyStartedAt: json['journey_started_at'] != null
          ? DateTime.tryParse(json['journey_started_at'].toString())
          : null,
      journeyEstimatedEndAt: json['journey_estimated_end_at'] != null
          ? DateTime.tryParse(json['journey_estimated_end_at'].toString())
          : null,
      isActive: json['is_active'] == true || status.toUpperCase() == 'IN_PROGRESS',
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
      ticketTripId: json['ticket_trip_id'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'route_id': routeId,
      'status': status,
      'booked_at': bookedAt?.toIso8601String(),
      'source': source,
      'destination': destination,
      'image_url': imageUrl,
      'ticket_code': ticketCode,
      'ticket_number': ticketNumber,
      'qr_payload': qrPayload,
      'qr_display': qrDisplay,
      'mode': mode,
      'mode_label': modeLabel,
      'color_hex': colorHex,
      'operator_name': operatorName,
      'class_name': className,
      'fare': fare,
      'source_type': sourceType,
      'travel_date': travelDate,
      'journey_started_at': journeyStartedAt?.toIso8601String(),
      'journey_estimated_end_at': journeyEstimatedEndAt?.toIso8601String(),
      'is_active': isActive,
      'distance_km': distanceKm,
      'ticket_trip_id': ticketTripId,
    };
  }

  Booking copyWith({int? ticketTripId, bool clearTrip = false}) {
    return Booking(
      id: id,
      userId: userId,
      routeId: routeId,
      status: status,
      bookedAt: bookedAt,
      source: source,
      destination: destination,
      imageUrl: imageUrl,
      ticketCode: ticketCode,
      ticketNumber: ticketNumber,
      qrPayload: qrPayload,
      qrDisplay: qrDisplay,
      mode: mode,
      modeLabel: modeLabel,
      colorHex: colorHex,
      operatorName: operatorName,
      className: className,
      fare: fare,
      sourceType: sourceType,
      travelDate: travelDate,
      journeyStartedAt: journeyStartedAt,
      journeyEstimatedEndAt: journeyEstimatedEndAt,
      isActive: isActive,
      distanceKm: distanceKm,
      ticketTripId: clearTrip ? null : (ticketTripId ?? this.ticketTripId),
    );
  }
}

class UserPassItem {
  final int id;
  final int passId;
  final String? name;
  final String? modeCoverage;
  final String? colorHex;
  final DateTime? validUntil;
  final String status;
  final double? price;

  UserPassItem({
    required this.id,
    required this.passId,
    this.name,
    this.modeCoverage,
    this.colorHex,
    this.validUntil,
    required this.status,
    this.price,
  });

  factory UserPassItem.fromJson(Map<String, dynamic> json) {
    return UserPassItem(
      id: json['id'] as int,
      passId: json['pass_id'] as int,
      name: json['name'] as String?,
      modeCoverage: json['mode_coverage'] as String?,
      colorHex: json['color_hex'] as String?,
      validUntil: json['valid_until'] != null
          ? DateTime.tryParse(json['valid_until'].toString())
          : null,
      status: json['status'] as String? ?? 'active',
      price: (json['price'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'pass_id': passId,
        'name': name,
        'mode_coverage': modeCoverage,
        'color_hex': colorHex,
        'valid_until': validUntil?.toIso8601String(),
        'status': status,
        'price': price,
      };
}

class TicketTrip {
  final int id;
  final int userId;
  final String name;
  final String? notes;
  final String? travelDate;
  final int ticketCount;
  final List<Booking> tickets;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  TicketTrip({
    required this.id,
    required this.userId,
    required this.name,
    this.notes,
    this.travelDate,
    this.ticketCount = 0,
    this.tickets = const [],
    this.createdAt,
    this.updatedAt,
  });

  factory TicketTrip.fromJson(Map<String, dynamic> json) {
    final tickets = (json['tickets'] as List? ?? [])
        .map((e) => Booking.fromJson(e as Map<String, dynamic>))
        .toList();
    return TicketTrip(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      name: json['name'] as String? ?? 'Trip',
      notes: json['notes'] as String?,
      travelDate: json['travel_date']?.toString(),
      ticketCount: (json['ticket_count'] as int?) ?? tickets.length,
      tickets: tickets,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'].toString())
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'name': name,
        'notes': notes,
        'travel_date': travelDate,
        'ticket_count': ticketCount,
        'tickets': tickets.map((t) => t.toJson()).toList(),
        'created_at': createdAt?.toIso8601String(),
        'updated_at': updatedAt?.toIso8601String(),
      };
}

class WalletData {
  final List<TicketTrip> trips;
  final List<Booking> tickets;
  final List<UserPassItem> passes;

  WalletData({
    this.trips = const [],
    required this.tickets,
    required this.passes,
  });

  factory WalletData.fromJson(Map<String, dynamic> json) {
    final trips = (json['trips'] as List? ?? [])
        .map((e) => TicketTrip.fromJson(e as Map<String, dynamic>))
        .toList();
    final tickets = (json['tickets'] as List? ?? [])
        .map((e) => Booking.fromJson(e as Map<String, dynamic>))
        .toList();
    final passes = (json['passes'] as List? ?? [])
        .map((e) => UserPassItem.fromJson(e as Map<String, dynamic>))
        .toList();
    return WalletData(trips: trips, tickets: tickets, passes: passes);
  }

  Map<String, dynamic> toJson() => {
        'trips': trips.map((t) => t.toJson()).toList(),
        'tickets': tickets.map((t) => t.toJson()).toList(),
        'passes': passes.map((p) => p.toJson()).toList(),
      };
}
