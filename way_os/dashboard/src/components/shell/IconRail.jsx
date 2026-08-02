import {
  ChartBar,
  ListChecks,
  MapPin,
  Notebook,
} from '@phosphor-icons/react';
import { motion } from 'motion/react';
import { useMotionBudget } from '../../motion/budget';
import './IconRail.css';

const TABS = [
  { id: 'overview', label: 'Overview', Icon: MapPin },
  { id: 'registries', label: 'Registries', Icon: Notebook },
  { id: 'operations', label: 'Operations', Icon: ListChecks },
  { id: 'insights', label: 'Insights', Icon: ChartBar },
];

export default function IconRail({ activeTab, onChange }) {
  const { reduce } = useMotionBudget();

  return (
    <nav className="icon-rail" aria-label="Primary">
      <div className="icon-rail__brand" title="TransitOS">
        <span>T</span>
      </div>
      <ul className="icon-rail__list">
        {TABS.map((tab) => {
          const active = activeTab === tab.id;
          const Icon = tab.Icon;
          return (
            <li key={tab.id}>
              <button
                type="button"
                className={`icon-rail__btn ${active ? 'is-active' : ''}`}
                onClick={() => onChange(tab.id)}
                title={tab.label}
                aria-label={tab.label}
                aria-current={active ? 'page' : undefined}
              >
                {active && !reduce && (
                  <motion.span
                    className="icon-rail__indicator"
                    layoutId="rail-indicator"
                    transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                  />
                )}
                {active && reduce && <span className="icon-rail__indicator" />}
                <Icon size={20} weight={active ? 'fill' : 'regular'} />
                <span className="icon-rail__label">{tab.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
