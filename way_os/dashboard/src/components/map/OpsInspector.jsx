import { motion } from 'motion/react';
import StatusPill from '../ui/StatusPill';
import { useMotionBudget } from '../../motion/budget';
import './OpsInspector.css';

export default function OpsInspector({
  vehicles,
  filters,
  onFiltersChange,
  selected,
  driver,
  route,
  onSelect,
  MODE_LABELS,
  STATUS_LABELS,
}) {
  const { panelSpring, reduce } = useMotionBudget();

  return (
    <motion.aside
      className="ops-inspector glass"
      initial={reduce ? false : { x: -28, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={reduce ? { opacity: 0 } : { x: -16, opacity: 0, transition: { duration: 0.14 } }}
      transition={panelSpring}
    >
      <div className="ops-inspector__filters">
        <label>
          Mode
          <select
            value={filters.mode}
            onChange={(e) => onFiltersChange({ ...filters, mode: e.target.value })}
          >
            <option value="all">All</option>
            {Object.entries(MODE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select
            value={filters.status}
            onChange={(e) => onFiltersChange({ ...filters, status: e.target.value })}
          >
            <option value="all">All</option>
            {Object.entries(STATUS_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="ops-inspector__list">
        {vehicles.map((v) => (
          <button
            key={v.id}
            type="button"
            className={`ops-inspector__row ${selected?.id === v.id ? 'is-active' : ''}`}
            onClick={() => onSelect(v.id)}
          >
            <div>
              <div className="ops-inspector__id">{v.id}</div>
              <div className="ops-inspector__sub">
                {MODE_LABELS[v.mode]} · {v.lastStop}
              </div>
            </div>
            <StatusPill status={v.status} label={STATUS_LABELS[v.status]} />
          </button>
        ))}
        {vehicles.length === 0 && (
          <div className="ops-inspector__empty">No vehicles match filters</div>
        )}
      </div>

      {selected ? (
        <motion.div
          className="ops-inspector__detail"
          key={selected.id}
          initial={reduce ? false : { opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduce ? 0 : 0.18, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="ops-inspector__detail-title">{selected.id}</div>
          <dl>
            <div>
              <dt>Route</dt>
              <dd>
                {route?.code} - {route?.name || '—'}
              </dd>
            </div>
            <div>
              <dt>Driver</dt>
              <dd>{driver?.name || 'Unassigned'}</dd>
            </div>
            <div>
              <dt>Occupancy</dt>
              <dd>{selected.occupancyPct}%</dd>
            </div>
            <div>
              <dt>On-time</dt>
              <dd>{selected.onTimePct}%</dd>
            </div>
            <div>
              <dt>Health</dt>
              <dd>{selected.healthScore}</dd>
            </div>
            <div>
              <dt>Seats</dt>
              <dd>{selected.seats}</dd>
            </div>
          </dl>
        </motion.div>
      ) : (
        <div className="ops-inspector__detail ops-inspector__detail--empty">
          Select a vehicle on the map or in the list
        </div>
      )}
    </motion.aside>
  );
}
