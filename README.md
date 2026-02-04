<div align="center">

```text
   ____  __  __ ____   ____ 
  / __ \ \ \/ // __ \ / __ \
 / / / /  \  // /_/ // / / /
/ /_/ /   / // _, _// /_/ / 
\___\_\  /_//_/ |_| \____/  
```

# Q Y R O

**The Universal Polyglot Runtime**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg?style=for-the-badge&color=00d4ff)](https://qyro.dev)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge&color=00ff9d)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Redis](https://img.shields.io/badge/redis-enabled-red.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Kafka](https://img.shields.io/badge/kafka-enabled-black.svg?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org)

<br/>

> **The Singularity for Code.**
> Write **Python, C, Rust, Go, Java, and TypeScript** in a *SINGLE* file.
> Orchestrate them with **Shared State (Redis)** and **Event Streams (Kafka)**.

[Getting Started](#getting-started) • [Features](#features) • [Architecture](#architecture) • [Example](#example) • [Documentation](#documentation)

</div>

---

## ⚡ What is Qyro?

**Qyro** (formerly Nexus) is a revolutionary runtime that breaks down language barriers. It allows you to define an entire distributed system—backend logic, high-performance kernels, and frontend UI—in a single `.qyro` file.

The **Orchestrator** parses this file, compiles native code (C/Rust/Go) on the fly, launches microservices, and connects them via a high-speed **Shared Memory Event Bus**.

### 🔥 Why Qyro?

*   **No Boilerplate**: Forget `Dockerfile`, `Makefile`, and complex build scripts.
*   **Unified State**: Access shared variables across Python and C as if they were in the same process.
*   **Industrial Strength**: Built on **Redis** for state persistence and **Kafka** for reliable messaging.
*   **Self-Healing**: Automatic process supervision with exponential backoff and crash recovery.

---

## 🚀 Architecture

Qyro isn't just a runner; it's a complete operating environment for polyglot applications.

```mermaid
graph TD
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

---

## 💻 Example

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

---

## 🌟 Features

### 🏳️‍🌈 True Polyglot Support
Support for a wide ecosystem of languages out of the box:
*   **Python**: Full support for data science and general logic.
*   **C / C++**: For high-performance system-level modules.
*   **Rust**: Memory-safe, blazing fast components.
*   **Go**: Concurrent networking services.
*   **Java**: Enterprise integration.
*   **TypeScript / Node.js**: Modern JavaScript operations.
*   **Web (React/Next.js)**: Full frontend framework integration.

### 🧠 Shared Memory Intelligence
*   **Zero-Latency Sharing**: Processes share data via Redis with local caching optimizations.
*   **Atomic Operations**: Safe headers for concurrent access.
*   **Persisted & Ephemeral**: Choose between in-memory speed or disk persistence.

### 📡 Event-Driven Backbone
*   **Kafka Integration**: Production-grade message streaming built-in.
*   **Redis Pub/Sub**: Lightweight real-time signaling.
*   **Broadcast API**: Send signals to all running modules simultaneously.

---

## 🛠️ Getting Started

### Prerequisites
*   **Python 3.8+**
*   **Redis 5.0+**
*   **Kafka 2.0+** (Optional, falls back to Redis)
*   **Docker** (Optional, for containerized runs)

### Installation

```bash
# Clone the repository
git clone https://github.com/qyro-dev/qyro.git
cd qyro

# Install dependencies
pip install -r requirements.txt
```

### Running Your First App

1.  **Start Infrastructure** (if not already running):
    ```bash
    docker-compose up -d redis kafka
    ```

2.  **Run the runtime**:
    ```bash
    python run.py examples/nexus_chat/main.nexus
    ```

    *Or run your own file:*
    ```bash
    python run.py my_app.qyro
    ```

---

## 📦 Directory Structure

*   📂 **`qyro/`**: The Core Package
    *   📂 **`orchestrator/`**: Process supervision and lifecycle management.
    *   📂 **`adapters/`**: Language-specific compilers and runners.
    *   📂 **`common/`**: Shared libraries, config, and parsing logic.
    *   📂 **`gateway/`**: API Gateway for external access.
    *   📂 **`cli/`**: Command Line Interface tools.

---

## 🤝 Contributing

We welcome all contributions to the Singularity!

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

<div align="center">

**Built with ❤️ by the Qyro Team**

*Code simpler. Build faster. Scale infinitely.*

</div>
