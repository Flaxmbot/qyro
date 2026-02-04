
import { PageHeader, Section } from '../components/Common';

export function Architecture() {
  return (
    <>
      <PageHeader
        title="Architecture"
        description="How Qyro orchestrates polyglot microservices."
      />

      <Section title="The Singularity (main.qyro)">
        <p>
          At the heart of Qyro is the "Singularity" file (`.qyro`). This file contains the definitions for:
        </p>
        <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
          <li><strong>Global Schema:</strong> Type definitions for shared memory.</li>
          <li><strong>Modules:</strong> Code blocks for different languages (Python, C, Rust, etc.).</li>
          <li><strong>Configuration:</strong> Resource limits and environment settings.</li>
        </ul>
      </Section>

      <Section title="Runtime Components">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          <div className="p-4 border border-border rounded-lg bg-surface">
            <h3 className="font-bold text-white mb-2">Orchestrator</h3>
            <p className="text-sm">Parses the Qyro file, compiles native code, and manages the lifecycle of all subprocesses.</p>
          </div>
          <div className="p-4 border border-border rounded-lg bg-surface">
            <h3 className="font-bold text-white mb-2">Redis Shared Memory</h3>
            <p className="text-sm">Acts as the central nervous system, allowing instant variable sharing between languages.</p>
          </div>
          <div className="p-4 border border-border rounded-lg bg-surface">
            <h3 className="font-bold text-white mb-2">Kafka Event Bus</h3>
            <p className="text-sm">Handles high-throughput, reliable messaging and event streaming between modules.</p>
          </div>
          <div className="p-4 border border-border rounded-lg bg-surface">
            <h3 className="font-bold text-white mb-2">API Gateway</h3>
            <p className="text-sm">Exposes the internal state and functions to the outside world via WebSocket and HTTP.</p>
          </div>
        </div>
      </Section>

      <Section title="Data Flow">
        <p>
          1. <strong>Source Code</strong> is parsed by the Qyro Parser.<br/>
          2. <strong>Native Code</strong> (C, Rust, Go) is compiled into binaries.<br/>
          3. <strong>Scripts</strong> (Python, TS) are prepared for execution.<br/>
          4. The <strong>Orchestrator</strong> launches all processes.<br/>
          5. Processes communicate via <strong>Redis</strong> (state) and <strong>Kafka</strong> (events).
        </p>
      </Section>
    </>
  );
}
