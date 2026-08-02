import { LayoutGroup } from 'motion/react';
import { TransitProvider } from './context/TransitContext';
import AppShell from './components/shell/AppShell';

export default function App() {
  return (
    <TransitProvider>
      <LayoutGroup>
        <AppShell />
      </LayoutGroup>
    </TransitProvider>
  );
}
