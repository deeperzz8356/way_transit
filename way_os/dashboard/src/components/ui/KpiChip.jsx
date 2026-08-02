import { motion } from 'motion/react';
import { useMotionBudget } from '../../motion/budget';
import './KpiChip.css';

export default function KpiChip({ label, value, trend, tone = 'neutral', index = 0 }) {
  const { fadeUp } = useMotionBudget();
  const motionProps = fadeUp(index * 0.05);

  return (
    <motion.div className={`kpi-chip kpi-chip--${tone}`} {...motionProps}>
      <div className="kpi-chip__label">{label}</div>
      <div className="kpi-chip__value">{value}</div>
      {trend && <div className="kpi-chip__trend">{trend}</div>}
    </motion.div>
  );
}
