import { AnimatePresence, motion } from 'motion/react';
import { X } from '@phosphor-icons/react';
import { useMotionBudget } from '../../motion/budget';
import './DetailDrawer.css';

export default function DetailDrawer({ open, onClose, title, subtitle, children }) {
  const { panelSpring, reduce } = useMotionBudget();

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.button
            type="button"
            className="drawer-backdrop"
            aria-label="Close detail"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduce ? 0 : 0.16 }}
            onClick={onClose}
          />
          <motion.aside
            className="detail-drawer"
            initial={reduce ? false : { x: '100%' }}
            animate={{ x: 0 }}
            exit={reduce ? { opacity: 0 } : { x: '100%', transition: { duration: 0.16 } }}
            transition={panelSpring}
          >
            <header className="detail-drawer__head">
              <div>
                <h2>{title}</h2>
                {subtitle && <p>{subtitle}</p>}
              </div>
              <button type="button" className="detail-drawer__close" onClick={onClose} aria-label="Close">
                <X size={16} weight="bold" />
              </button>
            </header>
            <div className="detail-drawer__body">{children}</div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

export function FieldGrid({ fields }) {
  return (
    <dl className="field-grid">
      {fields.map((f) => (
        <div key={f.label} className="field-grid__item">
          <dt>{f.label}</dt>
          <dd>{f.value ?? '—'}</dd>
        </div>
      ))}
    </dl>
  );
}
