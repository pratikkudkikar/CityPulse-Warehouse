import 'leaflet/dist/leaflet.css';
import { DemoOne } from './demo';
import { StateSatelliteMap } from '@/components/ui/state-satellite-map';

function App() {
  return (
    <main className="bg-black text-white min-h-screen">
      <DemoOne />
      <StateSatelliteMap />
    </main>
  );
}

export default App;
