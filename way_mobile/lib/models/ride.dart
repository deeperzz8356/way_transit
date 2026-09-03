class Ride {
  final int? id;
  final String source;
  final String destination;
  final String? driverName;
  final String? driverPhone;
  final String? driverImage;
  final double? driverRating;
  final int driverReviews;
  final String vehicleType; // 'bike', 'auto', 'car', 'premium'
  final String? vehiclePlate;
  final double fare;
  final int estimatedMinutes;
  final String status; // 'searching', 'confirmed', 'arrived', 'in_progress', 'completed', 'cancelled'
  final DateTime? createdAt;
  final DateTime? confirmedAt;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final String? otp;
  final double? currentLat;
  final double? currentLon;

  Ride({
    this.id,
    required this.source,
    required this.destination,
    this.driverName,
    this.driverPhone,
    this.driverImage,
    this.driverRating,
    this.driverReviews = 0,
    required this.vehicleType,
    this.vehiclePlate,
    required this.fare,
    required this.estimatedMinutes,
    required this.status,
    this.createdAt,
    this.confirmedAt,
    this.startedAt,
    this.completedAt,
    this.otp,
    this.currentLat,
    this.currentLon,
  });

  factory Ride.fromJson(Map<String, dynamic> json) {
    return Ride(
      id: json['id'],
      source: json['source'] ?? 'Unknown',
      destination: json['destination'] ?? 'Unknown',
      driverName: json['driver_name'],
      driverPhone: json['driver_phone'],
      driverImage: json['driver_image'],
      driverRating: (json['driver_rating'] as num?)?.toDouble(),
      driverReviews: json['driver_reviews'] ?? 0,
      vehicleType: json['vehicle_type'] ?? 'car',
      vehiclePlate: json['vehicle_plate'],
      fare: (json['fare'] as num?)?.toDouble() ?? 0.0,
      estimatedMinutes: json['estimated_minutes'] ?? 0,
      status: json['status'] ?? 'searching',
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
      confirmedAt: json['confirmed_at'] != null ? DateTime.parse(json['confirmed_at']) : null,
      startedAt: json['started_at'] != null ? DateTime.parse(json['started_at']) : null,
      completedAt: json['completed_at'] != null ? DateTime.parse(json['completed_at']) : null,
      otp: json['otp'],
      currentLat: (json['current_lat'] as num?)?.toDouble(),
      currentLon: (json['current_lon'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'source': source,
    'destination': destination,
    'driver_name': driverName,
    'driver_phone': driverPhone,
    'driver_image': driverImage,
    'driver_rating': driverRating,
    'driver_reviews': driverReviews,
    'vehicle_type': vehicleType,
    'vehicle_plate': vehiclePlate,
    'fare': fare,
    'estimated_minutes': estimatedMinutes,
    'status': status,
    'created_at': createdAt?.toIso8601String(),
    'confirmed_at': confirmedAt?.toIso8601String(),
    'started_at': startedAt?.toIso8601String(),
    'completed_at': completedAt?.toIso8601String(),
    'otp': otp,
    'current_lat': currentLat,
    'current_lon': currentLon,
  };
}
