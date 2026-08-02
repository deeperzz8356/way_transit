# TransitOS Operator Dashboard

Dark industrial command center for Tier-2 / metro transit operators. Mumbai mock dataset, map-first Overview (Pulse ↔ Ops), Registries, Operations, and Insights.

## Run

```bash
cd way_os/dashboard
npm install
npm run dev
```

Opens on [http://localhost:5174](http://localhost:5174).

## Stack

- Vite + React 18
- Motion for React (`motion/react`)
- Leaflet + react-leaflet (Carto Dark Matter basemap)

## Tabs

| Tab | Purpose |
|---|---|
| Overview | Map pulse with KPI overlays; toggle Ops for filters + inspector |
| Registries | Vehicles / Drivers / Network (routes + operators) |
| Operations | Dispatch board, digital checklist, trip log |
| Insights | Scorecards + AI-style recommendations |

Use the **Operator / Municipality** switch in the top bar to remap Overview KPIs and Insights framing.

## Note

All data is mock / local. No backend required for this demo.
