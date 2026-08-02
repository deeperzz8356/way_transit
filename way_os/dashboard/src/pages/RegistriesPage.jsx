import { useMemo, useState } from 'react';
import { useTransitData } from '../context/TransitContext';
import DataTable from '../components/ui/DataTable';
import DetailDrawer, { FieldGrid } from '../components/ui/DetailDrawer';
import StatusPill from '../components/ui/StatusPill';
import SegmentedControl from '../components/ui/SegmentedControl';
import './page.css';

export default function RegistriesPage() {
  const {
    vehicles,
    drivers,
    routes,
    operators,
    getDriver,
    getRoute,
    getOperator,
    MODE_LABELS,
    STATUS_LABELS,
  } = useTransitData();

  const [sub, setSub] = useState('vehicles');
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);

  const q = query.trim().toLowerCase();

  const vehicleRows = useMemo(
    () =>
      vehicles.filter(
        (v) =>
          !q ||
          v.id.toLowerCase().includes(q) ||
          v.mode.includes(q) ||
          (v.lastStop || '').toLowerCase().includes(q),
      ),
    [vehicles, q],
  );

  const driverRows = useMemo(
    () =>
      drivers.filter(
        (d) => !q || d.name.toLowerCase().includes(q) || d.license.toLowerCase().includes(q),
      ),
    [drivers, q],
  );

  const routeRows = useMemo(
    () =>
      routes.filter(
        (r) =>
          !q ||
          r.code.toLowerCase().includes(q) ||
          r.name.toLowerCase().includes(q) ||
          r.mode.includes(q),
      ),
    [routes, q],
  );

  const vehicleCols = [
    { key: 'id', label: 'Vehicle ID', render: (r) => <span className="mono">{r.id}</span> },
    { key: 'mode', label: 'Mode', render: (r) => MODE_LABELS[r.mode] },
    { key: 'route', label: 'Route', render: (r) => getRoute(r.routeId)?.code || '—' },
    { key: 'driver', label: 'Driver', render: (r) => getDriver(r.driverId)?.name || '—' },
    {
      key: 'status',
      label: 'Status',
      render: (r) => <StatusPill status={r.status} label={STATUS_LABELS[r.status]} />,
    },
    { key: 'seats', label: 'Seats' },
    { key: 'healthScore', label: 'Health' },
  ];

  const driverCols = [
    { key: 'name', label: 'Driver' },
    { key: 'vehicleId', label: 'Vehicle', render: (r) => <span className="mono">{r.vehicleId}</span> },
    { key: 'license', label: 'License', render: (r) => <span className="mono">{r.license}</span> },
    { key: 'performance', label: 'Score' },
    { key: 'rating', label: 'Rating' },
    {
      key: 'compliance',
      label: 'Compliance',
      render: (r) => <StatusPill status={r.compliance} label={r.compliance} />,
    },
    {
      key: 'status',
      label: 'Duty',
      render: (r) => <StatusPill status={r.status === 'on_duty' ? 'on_time' : 'idle'} label={r.status.replace('_', ' ')} />,
    },
  ];

  const routeCols = [
    { key: 'code', label: 'Code', render: (r) => <span className="mono">{r.code}</span> },
    { key: 'name', label: 'Route' },
    { key: 'mode', label: 'Mode', render: (r) => MODE_LABELS[r.mode] },
    { key: 'operator', label: 'Operator', render: (r) => getOperator(r.operatorId)?.shortName },
    { key: 'distanceKm', label: 'Km' },
    { key: 'fare', label: 'Fare', render: (r) => `₹${r.fare}` },
    { key: 'frequencyMin', label: 'Freq (min)' },
    { key: 'vehicleAllocation', label: 'Vehicles' },
  ];

  let drawerTitle = '';
  let drawerSubtitle = '';
  let drawerFields = [];

  if (selected?.type === 'vehicle') {
    const v = selected.data;
    drawerTitle = v.id;
    drawerSubtitle = `${MODE_LABELS[v.mode]} · ${getOperator(v.operatorId)?.name}`;
    drawerFields = [
      { label: 'Owner', value: v.owner },
      { label: 'Driver', value: getDriver(v.driverId)?.name },
      { label: 'Permit', value: v.permit },
      { label: 'Insurance', value: v.insurance },
      { label: 'Fitness', value: v.fitness },
      { label: 'Emission', value: v.emission },
      { label: 'Route', value: getRoute(v.routeId)?.name },
      { label: 'Seats', value: v.seats },
      { label: 'Accessibility', value: v.accessibility ? 'Yes' : 'No' },
      { label: 'Fuel', value: v.fuelType },
      { label: 'Age (yrs)', value: v.ageYears },
      { label: 'Health score', value: v.healthScore },
      { label: 'Maintenance', value: v.maintenanceScore },
      { label: 'On-time %', value: v.onTimePct },
      { label: 'Occupancy %', value: v.occupancyPct },
      { label: 'Trips today', value: v.tripsToday },
    ];
  } else if (selected?.type === 'driver') {
    const d = selected.data;
    drawerTitle = d.name;
    drawerSubtitle = d.license;
    drawerFields = [
      { label: 'License valid', value: d.licenseValid },
      { label: 'Training', value: d.training },
      { label: 'Assigned vehicle', value: d.vehicleId },
      { label: 'Route history', value: d.routeHistory.join(', ') },
      { label: 'Performance', value: d.performance },
      { label: 'Accidents', value: d.accidents },
      { label: 'Passenger rating', value: d.rating },
      { label: 'Hours today', value: d.hoursToday },
      { label: 'Compliance', value: d.compliance },
      { label: 'Duty status', value: d.status },
    ];
  } else if (selected?.type === 'route') {
    const r = selected.data;
    drawerTitle = `${r.code} · ${r.name}`;
    drawerSubtitle = getOperator(r.operatorId)?.name;
    drawerFields = [
      { label: 'Mode', value: MODE_LABELS[r.mode] },
      { label: 'Distance', value: `${r.distanceKm} km` },
      { label: 'Travel time', value: `${r.travelTimeMin} min` },
      { label: 'Peak demand', value: r.peakDemand },
      { label: 'Fare', value: `₹${r.fare}` },
      { label: 'Frequency', value: `${r.frequencyMin} min` },
      { label: 'Allocation', value: r.vehicleAllocation },
      { label: 'Stops', value: r.stops.map((s) => s.name).join(' → ') },
    ];
  }

  return (
    <div className="page page--scroll">
      <div className="page__toolbar">
        <div>
          <h2 className="page__title">Registries</h2>
          <p className="page__sub">Digitized vehicle, driver, and network records</p>
        </div>
        <div className="page__toolbar-right">
          <SegmentedControl
            value={sub}
            onChange={(v) => {
              setSub(v);
              setSelected(null);
              setQuery('');
            }}
            options={[
              { value: 'vehicles', label: 'Vehicles' },
              { value: 'drivers', label: 'Drivers' },
              { value: 'network', label: 'Network' },
            ]}
          />
          <input
            className="page__search"
            type="search"
            placeholder="Search records"
            aria-label="Search registry records"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </div>

      {sub === 'vehicles' && (
        <DataTable
          columns={vehicleCols}
          rows={vehicleRows}
          activeId={selected?.data?.id}
          onRowClick={(row) => setSelected({ type: 'vehicle', data: row })}
        />
      )}
      {sub === 'drivers' && (
        <DataTable
          columns={driverCols}
          rows={driverRows}
          activeId={selected?.data?.id}
          onRowClick={(row) => setSelected({ type: 'driver', data: row })}
        />
      )}
      {sub === 'network' && (
        <>
          <div className="ops-strip" style={{ marginBottom: 12 }}>
            {operators.map((op) => (
              <div key={op.id} className="ops-strip__card">
                <div className="ops-strip__label">{op.shortName}</div>
                <div className="ops-strip__value">{op.name}</div>
                <div className="ops-strip__meta">
                  Fleet {op.fleetSize} · Routes {op.routes} · Compliance {op.compliance}%
                </div>
              </div>
            ))}
          </div>
          <DataTable
            columns={routeCols}
            rows={routeRows}
            activeId={selected?.data?.id}
            onRowClick={(row) => setSelected({ type: 'route', data: row })}
          />
        </>
      )}

      <DetailDrawer
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        title={drawerTitle}
        subtitle={drawerSubtitle}
      >
        <FieldGrid fields={drawerFields} />
      </DetailDrawer>
    </div>
  );
}
