
import { PageHeader, Section, CodeBlock } from '../components/Common';

export function Polyglot() {
  return (
    <>
      <PageHeader
        title="Polyglot Runtime"
        description="Supported languages and integration patterns."
      />

      <Section title="Python">
        <p>Best for business logic, data processing, and scripting.</p>
        <CodeBlock
          language="python"
          code={`>>>python:logic
def process_data(data):
    return [x * 2 for x in data]`}
        />
      </Section>

      <Section title="C / C++">
        <p>Best for high-performance kernels and system-level operations. compiled with GCC/Clang.</p>
        <CodeBlock
          language="c"
          code={`>>>c:kernel
int compute(int x) {
    return x * x;
}`}
        />
      </Section>

      <Section title="Rust">
        <p>Best for safe, concurrent systems programming. Compiled with Cargo.</p>
        <CodeBlock
          language="rust"
          code={`>>>rs:safety
fn main() {
    println!("Safe and fast!");
}`}
        />
      </Section>

      <Section title="Go">
        <p>Best for networked services and concurrency.</p>
        <CodeBlock
          language="go"
          code={`>>>go:service
func main() {
    fmt.Println("Goroutines active")
}`}
        />
      </Section>
    </>
  );
}
