import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import IconRail from './IconRail';
import TopBar from './TopBar';
import { useTransitData } from '../../context/TransitContext';
import OverviewPage from '../../pages/OverviewPage';
import RegistriesPage from '../../pages/RegistriesPage';
import OperationsPage from '../../pages/OperationsPage';
import InsightsPage from '../../pages/InsightsPage';
import './AppShell.css';

const PAGES = {
  overview: OverviewPage,
  registries: RegistriesPage,
  operations: OperationsPage,
  insights: InsightsPage,
};

export default function AppShell() {
  const { activeTab, setActiveTab, role, setRole, CITY } = useTransitData();
  const reduceMotion = useReducedMotion();
  const Page = PAGES[activeTab] || OverviewPage;

  return (
    <div className="app-shell">
      <IconRail activeTab={activeTab} onChange={setActiveTab} />
      <div className="app-shell__main">
        <TopBar city={CITY} role={role} onRoleChange={setRole} />
        <div className="app-shell__content">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={activeTab}
              className="app-shell__page"
              initial={reduceMotion ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={reduceMotion ? undefined : { opacity: 0 }}
              transition={{ duration: reduceMotion ? 0 : 0.14, ease: [0.16, 1, 0.3, 1] }}
            >
              <Page />
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
