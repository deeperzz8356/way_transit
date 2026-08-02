import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class MapScreen extends StatelessWidget {
  const MapScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Example center location (Mumbai)
    const center = LatLng(19.0760, 72.8777);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Map'),
      ),
      body: FlutterMap(
        options: MapOptions(
          center: center,
          zoom: 13.0,
          // Enable all gestures: pinch to zoom, scroll wheel, drag, etc.
          interactiveFlags: InteractiveFlag.all,
          // Reasonable zoom limits for OSM tiles
          minZoom: 5,
          maxZoom: 18,
        ),
        children: [
          TileLayer(
            urlTemplate: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            subdomains: const ['a', 'b', 'c'],
            userAgentPackageName: 'com.example.way_mobile',
          ),
          MarkerLayer(
            markers: [
              Marker(
                    width: 40,
                    height: 40,
                    point: center,
                    child: const Icon(Icons.location_on, color: Colors.red, size: 40),
                  ),
            ],
          ),
        ],
      ),
    );
  }
}
