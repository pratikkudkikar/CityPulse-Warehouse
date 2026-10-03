import { DemoOne } from './demo';
import { StateSatelliteMap } from '@/components/ui/state-satellite-map';

export const LiveDemoPage = () => {
  return (
    <main className="bg-black text-white min-h-screen">
      <div className="sticky top-0 z-[60] w-full border-b border-zinc-800/80 bg-zinc-950/90 backdrop-blur px-4 py-3 text-center text-sm">
        Live Demo • Hero UI + State Satellite Map • Open at <strong>/live-demo</strong>
      </div>
      <DemoOne />
      <StateSatelliteMap />
    </main>
  );
};
