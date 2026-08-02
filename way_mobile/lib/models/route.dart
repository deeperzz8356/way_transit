class Route {
  final int id;
  final String source;
  final String destination;
  final String mode;
  final String time;
  final int price;

  Route({
    required this.id,
    required this.source,
    required this.destination,
    required this.mode,
    required this.time,
    required this.price,
  });

  factory Route.fromJson(Map<String, dynamic> json) {
    return Route(
      id: json['id'],
      source: json['source'],
      destination: json['destination'],
      mode: json['mode'],
      time: json['time'],
      price: json['price'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'source': source,
      'destination': destination,
      'mode': mode,
      'time': time,
      'price': price,
    };
  }
}
