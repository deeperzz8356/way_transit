import L from 'leaflet';

const MODE_COLORS = {
  bus: '#2dd4bf',
  mini_bus: '#38bdf8',
  shared_taxi: '#f5a623',
  auto: '#a78bfa',
};

const STATUS_RING = {
  on_time: '#2dd4bf',
  delayed: '#f5a623',
  maintenance: '#ef4444',
  idle: '#64748b',
};

export function createVehicleIcon(mode, status, selected = false) {
  const fill = MODE_COLORS[mode] || '#2dd4bf';
  const ring = STATUS_RING[status] || '#64748b';
  const size = selected ? 18 : 12;
  const ringW = selected ? 3 : 2;

  return L.divIcon({
    className: 'vehicle-marker',
    iconSize: [size + 8, size + 8],
    iconAnchor: [(size + 8) / 2, (size + 8) / 2],
    html: `<div style="
      width:${size}px;height:${size}px;border-radius:50%;
      background:${fill};border:${ringW}px solid ${ring};
      box-shadow:0 0 0 2px rgba(11,13,16,0.85);
      ${selected ? 'transform:scale(1.15);' : ''}
    "></div>`,
  });
}

export { MODE_COLORS, STATUS_RING };
