<div align="center">

<h1 align="center">
  <pre style="margin: 0; padding: 0; display: inline-block; animation: pulse 2s infinite;">
    <code style="font-family: monospace; white-space: pre; color: #00d4ff; text-shadow: 0 0 5px rgba(0,212,255,0.5);">
   ____  __  __ ____   ____
  / __ \ \ \/ // __ \ / __ \
 / / / /  \  // /_/ // / / /
/ /_/ /   / // _, _// /_/ /
\____/   /_//_/ |_|\____/
    </code>
  </pre>
  <br>
  <span style="display: inline-block; animation: pulse 2s infinite; font-family: monospace; font-weight: bold; font-size: 2em; background: linear-gradient(45deg, #00d4ff, #00ff9d, #ff00aa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; color: transparent;">Q Y R O</span>
  <br>
</h1>

<h3 align="center">The Universal Polyglot Runtime</h3>

<p align="center">
  <strong>Write Python, C, Rust, Go, Java, and TypeScript in a SINGLE file</strong>
  <br>
  <em>Orchestrate them with Shared State (Redis) and Event Streams (Kafka)</em>
</p>

<p align="center">
  <a href="https://github.com/Flaxmbot/qyro/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge&color=00ff9d" alt="License">
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/python-3.8+-yellow.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://redis.io">
    <img src="https://img.shields.io/badge/redis-enabled-red.svg?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  </a>
  <a href="https://kafka.apache.org">
    <img src="https://img.shields.io/badge/kafka-enabled-black.svg?style=for-the-badge&logo=apachekafka&logoColor=white" alt="Kafka">
  </a>
  <br>
  <a href="https://github.com/Flaxmbot/qyro/releases">
    <img src="https://img.shields.io/badge/version-2.0.0-blue.svg?style=for-the-badge&color=00d4ff" alt="Version">
  </a>
  <a href="https://github.com/Flaxmbot/qyro/actions/workflows/test.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/Flaxmbot/qyro/test.yml?style=for-the-badge&label=tests" alt="Tests">
  </a>
  <a href="https://github.com/Flaxmbot/qyro/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/Flaxmbot/qyro?style=for-the-badge&color=orange" alt="Contributors">
  </a>
</p>

</div>

<style>
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.animated-gradient {
  background: linear-gradient(45deg, #00d4ff, #00ff9d, #ff00aa, #00d4ff);
  background-size: 300% 300%;
  animation: gradient-animation 8s ease infinite;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
}

@keyframes gradient-animation {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.feature-card {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 10px;
  padding: 20px;
  margin: 10px;
  color: white;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.language-tag {
  display: inline-block;
  padding: 3px 8px;
  margin: 2px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: bold;
  background: #4a5568;
  color: white;
}
</style>

---

<div align="center">
  <h3>🚀 The Singularity for Code</h3>
  <p><em>Breaking down language barriers with shared state and event-driven architecture</em></p>
</div>

<div align="center">
  
[📖 Documentation](#documentation) • [⚡ Quick Start](#-quick-start) • [🏗️ Architecture](#%EF%B8%8F-architecture) • [💡 Examples](#-examples) • [🤝 Contributing](#-contributing)

</div>

---

## ✨ What is Qyro?

**Qyro** is a revolutionary runtime that breaks down language barriers. It allows you to define an entire distributed system—backend logic, high-performance kernels, and frontend UI—in a single `.qyro` file.

The **Orchestrator** parses this file, compiles native code (C/Rust/Go) on the fly, launches microservices, and connects them via a high-speed **Shared Memory Event Bus**.

### 🎯 Key Benefits

- **No Boilerplate**: Forget `Dockerfile`, `Makefile`, and complex build scripts
- **Unified State**: Access shared variables across Python and C as if they were in the same process
- **Industrial Strength**: Built on **Redis** for state persistence and **Kafka** for reliable messaging
- **Self-Healing**: Automatic process supervision with exponential backoff and crash recovery
- **Cross-Language**: Seamless integration between Python, C, Rust, Go, Java, and TypeScript
- **Real-Time**: Event-driven architecture with instant state synchronization

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Redis 5.0+** (for shared state)
- **Kafka 2.0+** (optional, for reliable messaging)
- **Docker** (optional, for containerized runs)

### Installation

```bash
# Clone the repository
git clone https://github.com/Flaxmbot/qyro.git
cd qyro

# Install dependencies
pip install -r requirements.txt

# Or install via pip
pip install qyro
```

### Running Your First App

1. **Start Infrastructure** (if not already running):
   ```bash
   docker-compose up -d redis kafka
   ```

2. **Run the runtime**:
   ```bash
   python run.py examples/basic_example.qyro
   ```

   *Or run your own file:*
   ```bash
   python run.py my_app.qyro
   ```

---

## 🏗️ Architecture

Qyro isn't just a runner; it's a complete operating environment for polyglot applications.

<div align="center">
  
```mermaid
graph TB
    subgraph "The Singularity (main.qyro)"
        Src[Source Code] -->|Parser| Parse[Qyro Parser]
    end

    Parse -->|Compiles| BinC[C/Rust/Go Binaries]
    Parse -->|Prepares| ScriptPy[Python/TS Scripts]

    subgraph "Runtime Environment"
        Orch[Qyro Orchestrator] -->|Supervises| P1[Process 1 (Python)]
        Orch -->|Supervises| P2[Process 2 (C/Rust)]
        Orch -->|Supervises| P3[Process 3 (Node)]

        P1 <-->|Read/Write| Redis[(Redis Shared State)]
        P2 <-->|Read/Write| Redis
        P3 <-->|Read/Write| Redis

        P1 <-->|Pub/Sub| Kafka{Kafka Event Bus}
        P2 <-->|Pub/Sub| Kafka

        GW[API Gateway] <-->|WS/HTTP| P1
    end

    style Orch fill:#f9f,stroke:#333,stroke-width:2px
    style Redis fill:#d50000,stroke:#333,stroke-width:2px,color:white
    style Kafka fill:#000,stroke:#333,stroke-width:2px,color:white
```

</div>

### Core Components

- **Parser**: Parses `.qyro` files and extracts code blocks by language
- **Compiler**: Compiles native code (C/Rust/Go) and prepares scripts (Python/TS)
- **Orchestrator**: Manages process lifecycle with supervision and crash recovery
- **Redis Memory**: Shared state system for inter-process communication
- **Kafka Manager**: Reliable messaging and event streaming
- **API Gateway**: HTTP/WebSocket interface for external access

---

## 💡 Examples

### Basic Example

Imagine a high-performance system where Python handles business logic while C handles raw computation, all synchronized instantly.

**`system.qyro`**
```python
>>>schema:global
# Shared memory definitions
current_load: int
system_status: string

>>>c:kernel
#include <stdio.h>
#include <stdlib.h>
// The C module calculates heavy loads
int main() {
    printf("KERNEL: logic circuit active\n");
    // Pseudo-code for shared memory access
    // set_shared_int("current_load", 99);
    return 0;
}

>>>py:brain
import time
from qyro.lib import shared_memory

def main():
    print("BRAIN: Monitoring system...")
    while True:
        # Read from the C kernel instantly
        load = shared_memory.get("current_load")
        print(f"BRAIN: Current load is {load}%")
        time.sleep(1)

if __name__ == "__main__":
    main()
```

### Advanced Example with Frontend

**`app.qyro`**
```python
>>>schema:global
user_count: int
messages: list

>>>py:backend
from qyro.lib import shared_memory
import time

def main():
    count = 0
    while True:
        shared_memory.set("user_count", count)
        count += 1
        time.sleep(5)

if __name__ == "__main__":
    main()

>>>react:frontend
import React, { useState, useEffect } from 'react';
import { useQyroState } from 'qyro-react';

function App() {
  const [userCount, setUserCount] = useQyroState('user_count');
  
  return (
    <div className="App">
      <h1>Real-time User Count: {userCount}</h1>
    </div>
  );
}

export default App;
```

---

## 🌟 Features

<div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div class="feature-card">
  <h3>🏳️‍🌈 True Polyglot Support</h3>
  <p>Seamless integration across multiple programming languages:</p>
  <div>
    <span class="language-tag">Python</span>
    <span class="language-tag">C/C++</span>
    <span class="language-tag">Rust</span>
    <span class="language-tag">Go</span>
    <span class="language-tag">Java</span>
    <span class="language-tag">TypeScript</span>
    <span class="language-tag">React</span>
  </div>
</div>

<div class="feature-card">
  <h3>🧠 Shared Memory Intelligence</h3>
  <ul style="text-align: left; margin-top: 10px;">
    <li>Zero-latency sharing via Redis</li>
    <li>Atomic operations for safety</li>
    <li>Persisted & ephemeral options</li>
    <li>Type-safe schema validation</li>
  </ul>
</div>

<div class="feature-card">
  <h3>📡 Event-Driven Backbone</h3>
  <ul style="text-align: left; margin-top: 10px;">
    <li>Kafka integration for reliability</li>
    <li>Redis Pub/Sub for signaling</li>
    <li>Broadcast API for all modules</li>
    <li>Guaranteed message delivery</li>
  </ul>
</div>

<div class="feature-card">
  <h3>🔒 Security & Resource Management</h3>
  <ul style="text-align: left; margin-top: 10px;">
    <li>Sandboxed execution</li>
    <li>CPU/memory constraints</li>
    <li>Configurable access control</li>
    <li>Automatic process supervision</li>
  </ul>
</div>

<div class="feature-card">
  <h3>📊 Monitoring & Observability</h3>
  <ul style="text-align: left; margin-top: 10px;">
    <li>Real-time metrics</li>
    <li>Centralized logging</li>
    <li>Built-in health checks</li>
    <li>Performance profiling</li>
  </ul>
</div>

</div>

---

## ⚙️ Configuration

Qyro can be configured via environment variables or command-line arguments:

```bash
python run.py app.qyro \
  --redis-host localhost \
  --redis-port 6379 \
  --kafka-bootstrap-servers localhost:9092 \
  --max-memory-mb 1024 \
  --max-restarts 10
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis server hostname | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `REDIS_PASSWORD` | Redis password (optional) | `None` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap servers | `localhost:9092` |
| `MAX_MEMORY_MB` | Max memory per process (MB) | `512` |
| `MAX_RESTARTS` | Max restart attempts per process | `5` |
| `DEBUG` | Enable debug mode | `false` |

---

## 📦 Directory Structure

```
qyro/
├── adapters/          # Language-specific compilers and runners
├── cli/              # Command Line Interface tools
├── common/           # Shared libraries, config, and parsing logic
├── gateway/          # API Gateway for external access
├── orchestrator/     # Process supervision and lifecycle management
└── ...
```

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=qyro

# Run specific test file
pytest tests/test_orchestrator.py
```

---

## 🤝 Contributing

We welcome all contributions to the Singularity!

### Development Setup

1. Fork the repository at [https://github.com/Flaxmbot/qyro](https://github.com/Flaxmbot/qyro)
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
4. Make your changes
5. Run tests:
   ```bash
   pytest tests/
   ```

### Contribution Guidelines

- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Submit a pull request with a clear description

### Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

Need help? Join our community:

- [GitHub Issues](https://github.com/Flaxmbot/qyro/issues) for bug reports and feature requests
- [Discord](https://discord.gg/qyro) for community discussions
- [Documentation](https://github.com/Flaxmbot/qyro/wiki) for detailed guides

---

<div align="center">

### 💖 Acknowledgments

Special thanks to the open-source community and all contributors who make Qyro possible.

<br>

<span class="animated-gradient"><strong>Built with ❤️ by the Qyro Team</strong></span>

<p class="animated-gradient" style="font-size: 1.2em; font-weight: bold;">Code simpler. Build faster. Scale infinitely.</p>

<br>

[![Star this project](https://img.shields.io/github/stars/Flaxmbot/qyro?style=social)](https://github.com/Flaxmbot/qyro)

</div>