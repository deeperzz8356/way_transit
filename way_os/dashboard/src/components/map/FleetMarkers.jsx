import { Marker, Popup, Polyline } from 'react-leaflet';
import { createVehicleIcon } from './VehicleMarker';
import { MODE_LABELS, STATUS_LABELS } from '../../data';

export default function VehicleMarkers({ vehicles, selectedId, onSelect, showTrails, getRoute }) {
  return (
    <>
      {vehicles.map((v) => {
        const label = `${v.id}, ${MODE_LABELS[v.mode]}, ${STATUS_LABELS[v.status]}, ${v.lastStop}`;
        return (
          <Marker
            key={v.id}
            position={[v.lat, v.lon]}
            title={label}
            alt={label}
            icon={createVehicleIcon(v.mode, v.status, selectedId === v.id)}
            eventHandlers={{
              click: () => onSelect?.(v.id),
            }}
          >
            <Popup>
              <strong>{v.id}</strong>
              <br />
              {MODE_LABELS[v.mode]} · {STATUS_LABELS[v.status]}
              <br />
              {v.lastStop}
            </Popup>
          </Marker>
        );
      })}
      {showTrails &&
        vehicles
          .filter((v) => v.status === 'on_time' || v.status === 'delayed')
          .slice(0, 8)
          .map((v) => {
            const route = getRoute?.(v.routeId);
            if (!route?.stops?.length) return null;
            const pts = route.stops.map((s) => [s.lat, s.lon]);
            return (
              <Polyline
                key={`trail-${v.id}`}
                positions={pts}
                pathOptions={{
                  color: v.status === 'delayed' ? '#e8a317' : '#2ec4b6',
                  weight: 2,
                  opacity: 0.35,
                  dashArray: '4 6',
                }}
              />
            );
          })}
    </>
  );
}
