import { createContext, useContext, useMemo, useState } from 'react';
import {
  vehicles,
  drivers,
  routes,
  operators,
  trips,
  dispatchBoard,
  checklistSteps,
  alerts,
  insights,
  kpis,
  getRoute,
  getDriver,
  getVehicle,
  getOperator,
  CITY,
  MUMBAI_CENTER,
  MODE_LABELS,
  STATUS_LABELS,
} from '../data';

const TransitContext = createContext(null);

export function TransitProvider({ children }) {
  const [role, setRole] = useState('operator');
  const [activeTab, setActiveTab] = useState('overview');
  const [mapMode, setMapMode] = useState('pulse');
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  const [dispatch, setDispatch] = useState(dispatchBoard);

  const selectedVehicle = useMemo(
    () => (selectedVehicleId ? getVehicle(selectedVehicleId) : null),
    [selectedVehicleId],
  );

  const activeKpis = role === 'municipality' ? kpis.municipality : kpis.operator;

  const value = useMemo(
    () => ({
      role,
      setRole,
      activeTab,
      setActiveTab,
      mapMode,
      setMapMode,
      selectedVehicleId,
      setSelectedVehicleId,
      selectedVehicle,
      vehicles,
      drivers,
      routes,
      operators,
      trips,
      dispatch,
      setDispatch,
      checklistSteps,
      alerts,
      insights,
      activeKpis,
      getRoute,
      getDriver,
      getVehicle,
      getOperator,
      CITY,
      MUMBAI_CENTER,
      MODE_LABELS,
      STATUS_LABELS,
    }),
    [role, activeTab, mapMode, selectedVehicleId, selectedVehicle, dispatch, activeKpis],
  );

  return <TransitContext.Provider value={value}>{children}</TransitContext.Provider>;
}

export function useTransitData() {
  const ctx = useContext(TransitContext);
  if (!ctx) throw new Error('useTransitData must be used within TransitProvider');
  return ctx;
}
