
import { PageHeader, Section, CodeBlock } from '../components/Common';

export function Reference() {
  return (
    <>
      <PageHeader
        title="API Reference"
        description="Interact with Qyro modules programmatically."
      />

      <Section title="Python API (qyro.lib)">
        <p>The standard library for Python modules.</p>
        <CodeBlock
          language="python"
          title="shared.py"
          code={`from qyro.lib import shared

# Read state
value = shared.get("key")

# Write state
shared.set("key", "value")

# Atomic operations
shared.incr("counter")`}
        />
      </Section>

      <Section title="C API (nexus.h)">
        <p>Native C bindings for high-performance access.</p>
        <CodeBlock
          language="c"
          title="nexus.h"
          code={`#include "nexus.h"

// Read state
int val = nexus_get_int("counter");

// Write state
nexus_set_int("counter", val + 1);`}
        />
      </Section>

      <Section title="Gateway API">
        <p>External REST endpoints provided by the API Gateway.</p>
        <CodeBlock
          language="json"
          title="GET /state"
          code={`{
  "status": "success",
  "data": {
    "counter": 42,
    "users": ["alice", "bob"]
  }
}`}
        />
      </Section>
    </>
  );
}
