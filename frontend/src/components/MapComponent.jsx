import React, { useEffect, useRef, useState } from 'react';

// Static coordinates map for pre-seeded transit cities
const CITY_COORDINATES = {
  mumbai: [19.0760, 72.8777],
  pune: [18.5204, 73.8567],
  bangalore: [12.9716, 77.5946],
  delhi: [28.7041, 77.1025]
};

// Colors for different transit modes
const TRANSIT_COLORS = {
  flight: '#3498db', // Blue
  train: '#27ae60',  // Green
  bus: '#e67e22',    // Orange
  cab: '#e74c3c'     // Red
};

export default function MapComponent({ source, destination, transport, centerCity = 'mumbai' }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);
  const polylineRef = useRef(null);
  const [coords, setCoords] = useState({ sourceCoords: null, destCoords: null });

  // Resolve coordinates for source and destination
  useEffect(() => {
    let active = true;

    async function resolveCoords() {
      const getCityCoords = async (city) => {
        if (!city) return null;
        const normalized = city.trim().toLowerCase();
        
        // Check static dictionary first
        if (CITY_COORDINATES[normalized]) {
          return CITY_COORDINATES[normalized];
        }

        // Fetch from OSM Nominatim API if online
        try {
          const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(city)}&limit=1`);
          const data = await res.json();
          if (data && data.length > 0) {
            return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
          }
        } catch (e) {
          console.warn("Geocoding failed for:", city, e);
        }
        
        // Fallback to center of India
        return [20.5937, 78.9629];
      };

      const sc = await getCityCoords(source);
      const dc = await getCityCoords(destination);

      if (active) {
        setCoords({ sourceCoords: sc, destCoords: dc });
      }
    }

    resolveCoords();

    return () => {
      active = false;
    };
  }, [source, destination]);

  // Map Initialization & Updates
  useEffect(() => {
    // Leaflet relies on global window.L loaded via CDN in index.html
    const L = window.L;
    if (!L) {
      console.error("Leaflet (L) is not loaded on the window object.");
      return;
    }

    // Fix marker icons default assets URL pathing issue in bundles
    const defaultIcon = L.icon({
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });
    L.Marker.prototype.options.icon = defaultIcon;

    // Set initial center coordinates
    const defaultCenter = CITY_COORDINATES[centerCity.toLowerCase()] || [19.0760, 72.8777];

    // Initialize Map Instance
    if (!mapInstance.current && mapRef.current) {
      mapInstance.current = L.map(mapRef.current, {
        zoomControl: true,
        scrollWheelZoom: true
      }).setView(defaultCenter, 6);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(mapInstance.current);
    }

    const map = mapInstance.current;
    if (!map) return;

    // Clear previous markers
    markersRef.current.forEach(marker => map.removeLayer(marker));
    markersRef.current = [];

    // Clear previous polyline
    if (polylineRef.current) {
      map.removeLayer(polylineRef.current);
      polylineRef.current = null;
    }

    const { sourceCoords, destCoords } = coords;

    if (sourceCoords && destCoords) {
      // 1. Draw Source & Destination Markers
      const sourceMarker = L.marker(sourceCoords)
        .bindPopup(`<b>Start:</b> ${source}`)
        .addTo(map);
      
      const destMarker = L.marker(destCoords)
        .bindPopup(`<b>End:</b> ${destination}`)
        .addTo(map);

      markersRef.current.push(sourceMarker, destMarker);

      // 2. Draw Polyline (Route Path)
      const color = TRANSIT_COLORS[transport?.toLowerCase()] || '#3498db';
      const isDashed = transport?.toLowerCase() === 'flight' || transport?.toLowerCase() === 'train';

      const polyline = L.polyline([sourceCoords, destCoords], {
        color: color,
        weight: 4,
        opacity: 0.8,
        dashArray: isDashed ? '8, 8' : null
      }).addTo(map);

      polylineRef.current = polyline;

      // 3. Fit Map viewport bounds to show both markers
      const bounds = L.latLngBounds([sourceCoords, destCoords]);
      map.fitBounds(bounds, { padding: [50, 50] });

    } else if (sourceCoords) {
      // Only source coordinates available (e.g. searching/default dashboard)
      const marker = L.marker(sourceCoords)
        .bindPopup(`<b>Location:</b> ${source}`)
        .addTo(map);
      markersRef.current.push(marker);
      map.setView(sourceCoords, 10);
    } else {
      // Fallback: zoom to default center if nothing is queried
      map.setView(defaultCenter, 6);
    }
  }, [coords, transport, centerCity]);

  // Clean up Map on Unmount
  useEffect(() => {
    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, []);

  return (
    <div 
      className="leaflet-map-wrapper"
      style={{ width: '100%', height: '100%', minHeight: '300px', borderRadius: 'inherit', zIndex: 1 }}
    >
      <div 
        ref={mapRef} 
        style={{ width: '100%', height: '100%', borderRadius: 'inherit' }}
      />
    </div>
  );
}
