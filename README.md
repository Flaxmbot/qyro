# Qyro 🌀

**The Universal Polyglot Runtime for SaaS**

Qyro is a minimalist runtime that lets you build polyglot distributed systems in a single file. It orchestrates Python, Rust, Java, Node.js, and Web components using Docker, with shared state (Redis) and event streaming (Kafka) built-in.

---

## 🚀 Features

*   **Single-File Microservices**: Define your entire stack in one `.qyro` file.
*   **Polyglot**: Support for Python, Rust, Java, Node.js/Web.
*   **Shared State**: Built-in `qyro.get()` and `qyro.set()` backed by Redis.
*   **Event Driven**: Built-in `qyro.publish()` and `qyro.subscribe()` backed by Kafka.
*   **SaaS CLI**: Beautiful, interactive terminal interface.
*   **VS Code Support**: Syntax highlighting for embedded languages.

---

## 📦 Installation

```bash
pip install .
```

Dependencies:
*   Docker Desktop (must be running)
*   Python 3.9+

---

## 🛠 Usage

### 1. Initialize a Project

```bash
qyro init myapp
cd myapp
```

### 2. Define Services (`myapp.qyro`)

```python
>>>web:frontend [react, axios]
import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function App() {
  const [msg, setMsg] = useState("");
  useEffect(() => {
    axios.get("http://localhost:8000/").then(r => setMsg(r.data.message));
  }, []);
  return <h1>{msg}</h1>;
}

>>>python:api [fastapi, uvicorn]
from fastapi import FastAPI
import qyro_adapters.python_adapter as qyro

app = FastAPI()

@app.get("/")
def root():
    # Use shared memory
    count = qyro.get("count") or 0
    qyro.set("count", int(count) + 1)
    return {"message": f"Hello from Python! Count: {count}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. Run

```bash
qyro run myapp.qyro
```

This will:
1.  Parse the `.qyro` file.
2.  Generate Dockerfiles, `docker-compose.yml`, and dependency manifests.
3.  Start Redis, Kafka, and your services.
4.  Stream logs to your terminal.

---

## 🧩 Language Support

### Python
*   **Header**: `>>>python:name [pip-deps]`
*   **Adapter**: `import qyro_adapters.python_adapter as qyro`

### Web (React/Next.js)
*   **Header**: `>>>web:name [npm-deps]`
*   **Adapter**: `import qyro from './qyro_adapters/js_adapter'` (if needed)
*   **Ports**: Automatically exposed on `3000`.

### Rust
*   **Header**: `>>>rust:name [crate-deps]`
*   **Adapter**: `mod qyro;` (injected helper)

### Java
*   **Header**: `>>>java:name [maven-deps]`
*   **Adapter**: `com.qyro.adapters.Qyro`

---

## 💻 VS Code Extension

1.  Open `vscode_extension/` folder.
2.  Run/Debug to install the extension.
3.  Enjoy syntax highlighting for all embedded languages!

---

## 🏗 Architecture

Qyro v3 compiles your intent into standard infrastructure:

*   **Orchestration**: Docker Compose
*   **State**: Redis (Shared Key-Value)
*   **Messaging**: Kafka (Pub/Sub)
*   **Networking**: Internal Docker bridge network `qyro-net`

---

## 📄 License

MIT
