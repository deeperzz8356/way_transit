import { useReducedMotion } from 'motion/react';

/** Shared Motion recipes — Emil-primary: fast, purposeful, reduced-motion safe */
export const EASE = [0.16, 1, 0.3, 1];

export function useMotionBudget() {
  const reduce = useReducedMotion();
  return {
    reduce,
    duration: (ms) => (reduce ? 0 : ms / 1000),
    fadeUp: (delay = 0) =>
      reduce
        ? { initial: false, animate: { opacity: 1, y: 0 }, transition: { duration: 0 } }
        : {
            initial: { opacity: 0, y: 8, filter: 'blur(4px)' },
            animate: { opacity: 1, y: 0, filter: 'blur(0px)' },
            transition: { duration: 0.22, delay, ease: EASE },
          },
    panelSpring: reduce
      ? { type: 'tween', duration: 0 }
      : { type: 'spring', stiffness: 420, damping: 36, mass: 0.8 },
    exitFast: reduce
      ? { opacity: 0 }
      : { opacity: 0, y: -4, transition: { duration: 0.12, ease: EASE } },
  };
}
