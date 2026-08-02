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
  final double? distanceKm;

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
    this.distanceKm,
  });

  factory Booking.fromJson(Map<String, dynamic> json) {
    String? source = json['source'] as String?;
    String? destination = json['destination'] as String?;
    final route = json['route'];
    if (route is Map<String, dynamic>) {
      source ??= route['source'] as String?;
      destination ??= route['destination'] as String?;
    }

    return Booking(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      routeId: json['route_id'] as int?,
      status: json['status'] as String? ?? 'CONFIRMED',
      bookedAt: json['booked_at'] != null
          ? DateTime.tryParse(json['booked_at'].toString())
          : null,
      source: source,
      destination: destination,
      imageUrl: json['image_url'] as String?,
      ticketCode: json['ticket_code'] as String?,
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
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
      'distance_km': distanceKm,
    };
  }
}
