import { useMemo, useState } from 'react';
import { MapContainer, TileLayer, ZoomControl } from 'react-leaflet';
import { AnimatePresence, motion } from 'motion/react';
import 'leaflet/dist/leaflet.css';
import { useTransitData } from '../../context/TransitContext';
import FleetMarkers from './FleetMarkers';
import MapOverlays, { SoftPreview } from './MapOverlays';
import OpsInspector from './OpsInspector';
import SegmentedControl from '../ui/SegmentedControl';
import { useMotionBudget } from '../../motion/budget';
import './FleetMap.css';

export default function FleetMap() {
  const {
    vehicles,
    mapMode,
    setMapMode,
    selectedVehicleId,
    setSelectedVehicleId,
    selectedVehicle,
    activeKpis,
    alerts,
    getDriver,
    getRoute,
    MODE_LABELS,
    STATUS_LABELS,
    MUMBAI_CENTER,
  } = useTransitData();

  const { reduce, duration } = useMotionBudget();
  const [filters, setFilters] = useState({ mode: 'all', status: 'all' });
  const [previewId, setPreviewId] = useState(null);

  const filtered = useMemo(() => {
    return vehicles.filter((v) => {
      if (filters.mode !== 'all' && v.mode !== filters.mode) return false;
      if (filters.status !== 'all' && v.status !== filters.status) return false;
      return true;
    });
  }, [vehicles, filters]);

  const topAlert = alerts.find((a) => a.priority === 'high') || alerts[0];
  const previewVehicle = previewId ? vehicles.find((v) => v.id === previewId) : null;

  const handleSelect = (id) => {
    if (mapMode === 'pulse') setPreviewId(id);
    else setSelectedVehicleId(id);
  };

  const enterOps = (vehicleId = null) => {
    setMapMode('ops');
    setPreviewId(null);
    const nextId = vehicleId || selectedVehicleId || filtered[0]?.id || vehicles[0]?.id;
    if (nextId) setSelectedVehicleId(nextId);
  };

  return (
    <div className={`fleet-map ${mapMode === 'pulse' ? 'fleet-map--pulse' : 'fleet-map--ops'}`}>
      <div className={`fleet-map__mode ${mapMode === 'ops' ? 'fleet-map__mode--ops' : ''} glass`}>
        <SegmentedControl
          layoutGroup="map-mode"
          value={mapMode}
          onChange={(v) => {
            if (v === 'ops') enterOps();
            else {
              setMapMode('pulse');
              setSelectedVehicleId(null);
              setPreviewId(null);
            }
          }}
          options={[
            { value: 'pulse', label: 'Pulse' },
            { value: 'ops', label: 'Ops' },
          ]}
        />
      </div>

      <ul className="fleet-map__legend glass" aria-label="Vehicle modes">
        <li><span className="dot dot--bus" /> Bus</li>
        <li><span className="dot dot--mini" /> Mini</li>
        <li><span className="dot dot--taxi" /> Taxi</li>
        <li><span className="dot dot--auto" /> Auto</li>
      </ul>

      <motion.div
        className="fleet-map__stage"
        animate={
          reduce
            ? undefined
            : {
                filter: mapMode === 'pulse' ? 'brightness(0.88) saturate(0.92)' : 'brightness(1) saturate(1)',
              }
        }
        transition={{ duration: duration(280), ease: [0.16, 1, 0.3, 1] }}
      >
        <MapContainer
          center={MUMBAI_CENTER}
          zoom={12}
          className="fleet-map__leaflet"
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          <ZoomControl position="bottomright" />
          <FleetMarkers
            vehicles={mapMode === 'ops' ? filtered : vehicles}
            selectedId={mapMode === 'ops' ? selectedVehicleId : previewId}
            onSelect={handleSelect}
            showTrails={mapMode === 'ops'}
            getRoute={getRoute}
          />
        </MapContainer>
      </motion.div>

      <MapOverlays
        mode={mapMode}
        kpis={activeKpis}
        alert={topAlert}
        onOpenAlert={() => {
          enterOps(topAlert.vehicleId);
        }}
      />

      {mapMode === 'pulse' && (
        <SoftPreview
          vehicle={previewVehicle}
          driver={previewVehicle ? getDriver(previewVehicle.driverId) : null}
          route={previewVehicle ? getRoute(previewVehicle.routeId) : null}
          onClose={() => setPreviewId(null)}
          onEnterOps={() => enterOps(previewId)}
        />
      )}

      <AnimatePresence>
        {mapMode === 'ops' && (
          <OpsInspector
            key="ops-inspector"
            vehicles={filtered}
            filters={filters}
            onFiltersChange={setFilters}
            selected={selectedVehicle}
            driver={selectedVehicle ? getDriver(selectedVehicle.driverId) : null}
            route={selectedVehicle ? getRoute(selectedVehicle.routeId) : null}
            onSelect={setSelectedVehicleId}
            MODE_LABELS={MODE_LABELS}
            STATUS_LABELS={STATUS_LABELS}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
