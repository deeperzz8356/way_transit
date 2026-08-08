class User {
  final int id;
  final String? email;
  final String? phone;
  final String? name;
  final String? googleId;
  final String? profileImage;
  final String? authProvider;
  final bool isVerified;
  final String? createdAt;
  final String? updatedAt;

  User({
    required this.id,
    this.email,
    this.phone,
    this.name,
    this.googleId,
    this.profileImage,
    this.authProvider,
    this.isVerified = false,
    this.createdAt,
    this.updatedAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      email: json['email'] as String?,
      phone: json['phone'] as String?,
      name: json['name'] as String?,
      googleId: json['google_id'] as String?,
      profileImage: json['profile_image'] as String?,
      authProvider: json['auth_provider'] as String?,
      isVerified: json['is_verified'] as bool? ?? false,
      createdAt: json['created_at']?.toString(),
      updatedAt: json['updated_at']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'phone': phone,
      'name': name,
      'google_id': googleId,
      'profile_image': profileImage,
      'auth_provider': authProvider,
      'is_verified': isVerified,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}
