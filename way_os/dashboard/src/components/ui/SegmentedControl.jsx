import { motion } from 'motion/react';
import { useMotionBudget } from '../../motion/budget';
import './SegmentedControl.css';

export default function SegmentedControl({ options, value, onChange, size = 'md', layoutGroup = 'seg' }) {
  const { reduce } = useMotionBudget();

  return (
    <div className={`seg seg--${size}`} role="tablist">
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            role="tab"
            aria-selected={active}
            className={`seg__btn ${active ? 'is-active' : ''}`}
            onClick={() => onChange(opt.value)}
          >
            {active && !reduce && (
              <motion.span
                className="seg__pill"
                layoutId={`${layoutGroup}-pill`}
                transition={{ type: 'spring', stiffness: 480, damping: 38, mass: 0.7 }}
              />
            )}
            {active && reduce && <span className="seg__pill" />}
            <span className="seg__label">{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
