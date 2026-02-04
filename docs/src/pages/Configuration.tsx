
import { PageHeader, Section, CodeBlock } from '../components/Common';

export function Configuration() {
  return (
    <>
      <PageHeader
        title="Configuration"
        description="Fine-tune the Qyro runtime environment."
      />

      <Section title="Environment Variables">
        <p>Qyro can be configured using the following environment variables:</p>

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border bg-surfaceHighlight">
                <th className="p-3 font-semibold text-white">Variable</th>
                <th className="p-3 font-semibold text-white">Description</th>
                <th className="p-3 font-semibold text-white">Default</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-border">
                <td className="p-3 font-mono text-sm text-primary">REDIS_HOST</td>
                <td className="p-3 text-sm">Redis server hostname</td>
                <td className="p-3 font-mono text-sm text-textMuted">localhost</td>
              </tr>
              <tr className="border-b border-border">
                <td className="p-3 font-mono text-sm text-primary">REDIS_PORT</td>
                <td className="p-3 text-sm">Redis server port</td>
                <td className="p-3 font-mono text-sm text-textMuted">6379</td>
              </tr>
              <tr className="border-b border-border">
                <td className="p-3 font-mono text-sm text-primary">KAFKA_BOOTSTRAP_SERVERS</td>
                <td className="p-3 text-sm">Kafka connection string</td>
                <td className="p-3 font-mono text-sm text-textMuted">localhost:9092</td>
              </tr>
              <tr className="border-b border-border">
                <td className="p-3 font-mono text-sm text-primary">MAX_MEMORY_MB</td>
                <td className="p-3 text-sm">Max memory per process</td>
                <td className="p-3 font-mono text-sm text-textMuted">512</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Command Line Arguments">
        <p>You can also pass arguments directly to the runner:</p>
        <CodeBlock
          language="bash"
          code={`python run.py app.qyro --redis-host 10.0.0.1 --kafka-bootstrap-servers kafka:9092`}
        />
      </Section>
    </>
  );
}
