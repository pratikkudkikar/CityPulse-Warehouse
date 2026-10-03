import 'leaflet/dist/leaflet.css';
import { LiveDemoPage } from './live-demo-page';

function App() {
  const path = typeof window !== 'undefined' ? window.location.pathname : '/';

  if (path === '/live-demo' || path === '/live-demo/') {
    return <LiveDemoPage />;
  }

  return <LiveDemoPage />;
}

export default App;
