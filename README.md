<div align="center">
  <img src="docs/assets/qyro_logo.svg" alt="Qyro Logo" width="600">

  <p align="center">
    <b>The Universal Polyglot Runtime</b>
    <br>
    Write Python, C, Rust, Go, Java, and TypeScript in a <i>single file</i> with shared state and event streams.
  </p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![Redis](https://img.shields.io/badge/redis-enabled-red.svg)](https://redis.io/)
  [![Kafka](https://img.shields.io/badge/kafka-streaming-black.svg)](https://kafka.apache.org/)
  [![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
</div>

---

<div align="center">
  <img src="docs/assets/terminal_demo.svg" alt="Qyro Terminal Demo" width="800">
</div>

---

## 🚀 The Singularity for Code

**Qyro** breaks down language barriers. It allows you to define an entire distributed system—backend logic, high-performance kernels, and frontend UI—in a single `.qyro` file.

The **Qyro Orchestrator** parses this file, compiles native code (C/Rust/Go) on the fly, launches microservices, and connects them via a high-speed **Shared Memory Event Bus** (Redis) and **Reliable Event Streaming** (Kafka).

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🏳️‍🌈 Polyglot** | Mix Python, C, Rust, Go, Java, TypeScript, and React in one file. |
| **🧠 Shared State** | Zero-latency variable sharing across languages via Redis. |
| **📡 Event Driven** | Built-in Kafka integration for reliable, scalable messaging. |
| **🛡️ Self-Healing** | Automatic process supervision, crash detection, and exponential backoff. |
| **⚡ High Performance** | Compile native modules on-the-fly for critical paths. |
| **🌐 API Gateway** | Integrated WebSocket/HTTP gateway for external access. |

---

## 🏗️ Architecture

Qyro isn't just a runner; it's a complete operating environment.

```mermaid
graph TD
    %% Styling
    classDef core fill:#1e1e1e,stroke:#00d4ff,stroke-width:2px,color:#fff
    classDef polyglot fill:#2d2d2d,stroke:#00ff9d,stroke-width:2px,color:#fff
    classDef store fill:#1e1e1e,stroke:#ff00aa,stroke-width:2px,color:#fff
    classDef stream fill:#1e1e1e,stroke:#fff,stroke-width:2px,color:#fff

    subgraph Singularity["The Singularity (main.qyro)"]
        direction TB
        Src["Source Code"] -->|Parser| Parse["Qyro Parser"]
    end

    Parse -->|Compiles| BinC["C/Rust/Go Binaries"]
    Parse -->|Prepares| ScriptPy["Python/TS Scripts"]

    subgraph Runtime["Runtime Environment"]
        direction TB
        Orch["Qyro Orchestrator"]

        P1["Process 1 (Python)"]
        P2["Process 2 (C/Rust)"]
        P3["Process 3 (Node)"]

        Orch -->|Supervises| P1
        Orch -->|Supervises| P2
        Orch -->|Supervises| P3

        GW["API Gateway"] <-->|WS/HTTP| P1
    end

    P1 <-->|Read/Write| Redis[("Redis Shared State")]
    P2 <-->|Read/Write| Redis
    P3 <-->|Read/Write| Redis

    P1 <-->|Pub/Sub| Kafka{"Kafka Event Bus"}
    P2 <-->|Pub/Sub| Kafka

    %% Apply styles
    class Src,Parse,Orch,GW core
    class P1,P2,P3,BinC,ScriptPy polyglot
    class Redis store
    class Kafka stream
```

---

## ⚡ Quick Start

### Prerequisites
*   Python 3.8+
*   Redis (Optional, for shared state)
*   Kafka (Optional, for event streaming)

### Installation

```bash
git clone https://github.com/qyro-dev/qyro.git
cd qyro
pip install -r requirements.txt
```

### Running Your First App

Create a file named `hello.qyro`:

```python
>>>schema:global
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
    printf("C Module: Watching shared memory...\n");
    while(1) {
        // Pseudo-code for brevity
        sleep(1);
    }
    return 0;
}
```

Run it:

```bash
python run.py hello.qyro
```

---

## 📚 Documentation

Detailed documentation is available in the [Wiki](https://github.com/qyro-dev/qyro/wiki).

*   [Language Reference](https://github.com/qyro-dev/qyro/wiki/Language-Reference)
*   [API Guide](https://github.com/qyro-dev/qyro/wiki/API-Guide)
*   [Deployment](https://github.com/qyro-dev/qyro/wiki/Deployment)

---

<div align="center">
  <sub>Built with ❤️ by the Qyro Team. Code simpler. Build faster. Scale infinitely.</sub>
</div>
