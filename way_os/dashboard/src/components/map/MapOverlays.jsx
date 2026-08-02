import { motion, AnimatePresence } from 'motion/react';
import { Warning } from '@phosphor-icons/react';
import KpiChip from '../ui/KpiChip';
import { useMotionBudget } from '../../motion/budget';
import './MapOverlays.css';

export default function MapOverlays({ mode, kpis, alert, onOpenAlert }) {
  const { reduce, duration } = useMotionBudget();

  return (
    <div className="map-overlays">
      <AnimatePresence>
        {mode === 'pulse' && (
          <motion.div
            key="pulse-chrome"
            className="map-overlays__pulse"
            initial={reduce ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={reduce ? undefined : { opacity: 0, transition: { duration: 0.12 } }}
            transition={{ duration: duration(200) }}
          >
            <div className="map-overlays__kpis">
              {kpis.slice(0, 4).map((kpi, i) => (
                <KpiChip
                  key={kpi.id}
                  label={kpi.label}
                  value={kpi.value}
                  trend={kpi.trend}
                  tone={kpi.tone}
                  index={i}
                />
              ))}
            </div>
            {alert && (
              <motion.button
                type="button"
                className={`map-overlays__alert glass map-overlays__alert--${alert.priority}`}
                initial={reduce ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: reduce ? 0 : 0.18, duration: duration(220), ease: [0.16, 1, 0.3, 1] }}
                onClick={onOpenAlert}
              >
                <Warning size={16} weight="fill" className="map-overlays__alert-icon" />
                <span>
                  <strong>{alert.vehicleId}</strong> {alert.issue}
                </span>
              </motion.button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function SoftPreview({ vehicle, driver, route, onClose, onEnterOps }) {
  const { reduce, duration } = useMotionBudget();

  return (
    <AnimatePresence>
      {vehicle && (
        <motion.div
          className="soft-preview glass"
          initial={reduce ? false : { opacity: 0, y: 12, filter: 'blur(4px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          exit={reduce ? { opacity: 0 } : { opacity: 0, y: 6, transition: { duration: 0.12 } }}
          transition={{ duration: duration(220), ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="soft-preview__head">
            <strong>{vehicle.id}</strong>
            <button type="button" onClick={onClose} aria-label="Dismiss preview">
              ×
            </button>
          </div>
          <p>
            {route?.name || 'Unassigned'} · {driver?.name || 'No driver'}
          </p>
          <p className="soft-preview__meta">
            Last stop {vehicle.lastStop} · Occupancy {vehicle.occupancyPct}%
          </p>
          <button type="button" className="soft-preview__cta" onClick={onEnterOps}>
            Open in Ops
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
