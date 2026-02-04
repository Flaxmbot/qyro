
import { Hero, FeatureGrid } from '../components/Hero';

export function Home() {
  return (
    <>
      <Hero />
      <div className="my-20">
        <h2 className="text-3xl font-bold text-center mb-12">Built for Modern Distributed Systems</h2>
        <FeatureGrid />
      </div>
    </>
  );
}
