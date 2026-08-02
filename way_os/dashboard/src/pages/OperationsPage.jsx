import { useMemo, useState } from 'react';
import { useTransitData } from '../context/TransitContext';
import DataTable from '../components/ui/DataTable';
import StatusPill from '../components/ui/StatusPill';
import './page.css';

const STEP_LABELS = {
  available: 'Available',
  fuel: 'Fuel',
  tyre: 'Tyre',
  brake: 'Brake',
  lights: 'Lights',
  driver: 'Driver',
  ready: 'Ready',
};

export default function OperationsPage() {
  const {
    dispatch,
    setDispatch,
    trips,
    checklistSteps,
    getVehicle,
    getDriver,
    getRoute,
  } = useTransitData();

  const [activeId, setActiveId] = useState(dispatch[2]?.id || dispatch[0]?.id);

  const active = dispatch.find((d) => d.id === activeId);

  const advanceChecklist = () => {
    if (!active) return;
    const idx = checklistSteps.indexOf(active.checklist);
    if (idx < 0 || idx >= checklistSteps.length - 1) return;
    const next = checklistSteps[idx + 1];
    setDispatch((prev) =>
      prev.map((d) =>
        d.id === active.id
          ? {
              ...d,
              checklist: next,
              status: next === 'ready' ? 'ready' : d.status === 'queued' ? 'pre_trip' : d.status,
            }
          : d,
      ),
    );
  };

  const dispatchCols = [
    { key: 'slot', label: 'Slot', render: (r) => <span className="mono">{r.slot}</span> },
    { key: 'vehicleId', label: 'Vehicle', render: (r) => <span className="mono">{r.vehicleId}</span> },
    { key: 'driver', label: 'Driver', render: (r) => getDriver(r.driverId)?.name || '—' },
    { key: 'route', label: 'Route', render: (r) => getRoute(r.routeId)?.code || '—' },
    {
      key: 'checklist',
      label: 'Checklist',
      render: (r) => STEP_LABELS[r.checklist] || r.checklist,
    },
    {
      key: 'status',
      label: 'Status',
      render: (r) => <StatusPill status={r.status} label={r.status.replace(/_/g, ' ')} />,
    },
  ];

  const tripCols = [
    { key: 'id', label: 'Trip', render: (r) => <span className="mono">{r.id}</span> },
    { key: 'vehicleId', label: 'Vehicle', render: (r) => <span className="mono">{r.vehicleId}</span> },
    { key: 'route', label: 'Route', render: (r) => getRoute(r.routeId)?.code },
    { key: 'departedAt', label: 'Departed' },
    {
      key: 'status',
      label: 'Status',
      render: (r) => <StatusPill status={r.status} label={r.status.replace(/_/g, ' ')} />,
    },
    { key: 'passengers', label: 'Pax' },
    {
      key: 'onTime',
      label: 'On time',
      render: (r) => (
        <StatusPill status={r.onTime ? 'on_time' : 'delayed'} label={r.onTime ? 'Yes' : 'No'} />
      ),
    },
  ];

  const stepIndex = active ? checklistSteps.indexOf(active.checklist) : -1;

  const activeMeta = useMemo(() => {
    if (!active) return null;
    return {
      vehicle: getVehicle(active.vehicleId),
      driver: getDriver(active.driverId),
      route: getRoute(active.routeId),
    };
  }, [active, getVehicle, getDriver, getRoute]);

  return (
    <div className="page page--scroll">
      <div className="page__toolbar">
        <div>
          <h2 className="page__title">Operations</h2>
          <p className="page__sub">Dispatch, pre-trip checklist, and trip log</p>
        </div>
      </div>

      <div className="ops-layout">
        <section className="ops-panel">
          <h3 className="section-title">Today's dispatch</h3>
          <DataTable
            columns={dispatchCols}
            rows={dispatch}
            activeId={activeId}
            onRowClick={(row) => setActiveId(row.id)}
          />
        </section>

        <section className="ops-panel ops-panel--side">
          <h3 className="section-title">Digital checklist</h3>
          {active ? (
            <>
              <div className="checklist-meta">
                <div className="mono">{active.vehicleId}</div>
                <div>
                  {activeMeta?.route?.name || '—'} · {activeMeta?.driver?.name || 'No driver'}
                </div>
              </div>
              <ol className="checklist">
                {checklistSteps.map((step, i) => {
                  const done = i < stepIndex || (stepIndex === checklistSteps.length - 1 && i === stepIndex);
                  const current = i === stepIndex && stepIndex < checklistSteps.length - 1;
                  const readyDone = stepIndex === checklistSteps.length - 1;
                  return (
                    <li
                      key={step}
                      className={`checklist__step ${done || (readyDone && i <= stepIndex) ? 'is-done' : ''} ${current ? 'is-current' : ''}`}
                    >
                      <span className="checklist__index">{i + 1}</span>
                      <span>{STEP_LABELS[step]}</span>
                    </li>
                  );
                })}
              </ol>
              <button
                type="button"
                className="checklist__advance"
                disabled={stepIndex < 0 || stepIndex >= checklistSteps.length - 1 || active.status === 'blocked'}
                onClick={advanceChecklist}
              >
                {stepIndex >= checklistSteps.length - 1 ? 'Ready for dispatch' : `Mark ${STEP_LABELS[checklistSteps[stepIndex]]} complete`}
              </button>
            </>
          ) : (
            <p className="page__sub">Select a dispatch row</p>
          )}
        </section>
      </div>

      <section className="ops-panel ops-panel--log">
        <h3 className="section-title">Trip log</h3>
        <DataTable columns={tripCols} rows={trips} />
      </section>
    </div>
  );
}
