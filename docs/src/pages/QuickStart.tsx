
import { PageHeader, Section, CodeBlock } from '../components/Common';

export function QuickStart() {
  return (
    <>
      <PageHeader
        title="Quick Start"
        description="Get up and running with Qyro in minutes."
      />

      <Section title="Prerequisites">
        <p>Before you begin, ensure you have the following installed:</p>
        <ul className="list-disc list-inside space-y-2 ml-4">
          <li>Python 3.8 or higher</li>
          <li>Redis (Optional, for shared state)</li>
          <li>Kafka (Optional, for event streaming)</li>
        </ul>
      </Section>

      <Section title="Installation">
        <p>Install Qyro using pip:</p>
        <CodeBlock
          language="bash"
          code={`pip install qyro`}
        />
        <p>Or clone the repository:</p>
        <CodeBlock
          language="bash"
          code={`git clone https://github.com/qyro-dev/qyro.git
cd qyro
pip install -r requirements.txt`}
        />
      </Section>

      <Section title="Your First App">
        <p>Create a file named <code>hello.qyro</code> with the following content:</p>
        <CodeBlock
          language="python"
          title="hello.qyro"
          code={`>>>schema:global
# Define shared state variables
counter: int

>>>python:p1
import time
from qyro.lib import shared
print("Python: Starting counter...")
while True:
    val = shared.get("counter") or 0
    shared.set("counter", val + 1)
    time.sleep(1)

>>>c:p2
#include <stdio.h>
// C code runs natively!
int main() {
    printf("C Module: Watching shared memory...\\n");
    while(1) {
        // Pseudo-code for brevity
        sleep(1);
    }
    return 0;
}`}
        />
      </Section>

      <Section title="Run It">
        <p>Execute your Qyro application:</p>
        <CodeBlock
          language="bash"
          code={`python run.py hello.qyro`}
        />
      </Section>
    </>
  );
}
