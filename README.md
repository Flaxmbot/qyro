<div align="center">

# <span style="font-family: 'Courier New', monospace;">██████╗ ██╗   ██╗ ██████╗ ███████╗████████╗███████╗</span>
# <span style="font-family: 'Courier New', monospace;">██╔══██╗╚██╗ ██╔╝██╔═══██╗██╔════╝╚══██╔══╝██╔════╝</span>
# <span style="font-family: 'Courier New', monospace;">██████╔╝ ╚████╔╝ ██║   ██║███████╗   ██║   █████╗  </span>
# <span style="font-family: 'Courier New', monospace;">██╔══██╗  ╚██╔╝  ██║   ██║╚════██║   ██║   ██╔══╝  </span>
# <span style="font-family: 'Courier New', monospace;">██████╔╝   ██║   ╚██████╔╝███████║   ██║   ███████╗</span>
# <span style="font-family: 'Courier New', monospace;">╚═════╝    ╚═╝    ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝</span>

### The Universal Polyglot Runtime
**Write Python, C, Rust, Java in one file with shared state and modern microservices architecture**

[![PyPI version](https://badge.fury.io/py/qyro.svg)](https://badge.fury.io/py/qyro)
[![Downloads](https://pepy.tech/badge/qyro)](https://pepy.tech/project/qyro)
[![License](https://img.shields.io/github/license/qyro-dev/qyro)](https://github.com/qyro-dev/qyro/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/qyro.svg)](https://pypi.org/project/qyro/)
[![Status](https://img.shields.io/pypi/status/qyro.svg)](https://pypi.org/project/qyro/)

</div>

---

## 🎯 **Animation Showcase**

<div align="center">
  
```python
import qyro
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
import time

console = Console()

# Animated Header
ascii_art = r"""
  _   _ ________   __  _______  _____
  | \ | |  ____\ \ / / |__   __||_   _|
  |  \| | |__   \ V /     | |     | |
  | . ` |  __|   > <      | |     | |
  | |\  | |____ / . \     | |    _| |_
  |_| \_|______/_/ \_\    |_|   |_____|

  Polyglot Runtime v2.0 - NBP v3 Protocol
"""

header_text = Text(ascii_art, style="bold cyan")
subtitle = Text("\nPolyglot Runtime v2.0 - NBP v3 Protocol", style="bold magenta")
console.print(header_text, end="")
console.print(subtitle)

# Animated Loading
spinner = Spinner("clock", style="cyan")
text = Text("Initializing The Singularity", style="bold yellow")
panel = Panel(spinner, title=text, border_style="yellow")

with Live(panel, refresh_per_second=20):
    time.sleep(2)  # Simulate initialization

console.print("[bold green]Singularity Active![/bold green]")
```

</div>

---

## ✨ **Features**

<div align="center">

| Feature | Description |
|--------|-------------|
| 🐍 **Polyglot Programming** | Write Python, C, Rust, Java, Go, JavaScript, TypeScript, and React in a single file |
| 🔄 **Shared State** | Real-time state sharing between different language modules |
| 📡 **Modern Messaging** | Built-in Kafka integration for reliable message passing |
| 🏗️ **Microservices Architecture** | Container-native design with service discovery |
| 🔌 **Language Adapters** | Seamless integration between different programming languages |
| 🔄 **Hot Reloading** | Automatic reloading during development |
| 🚀 **Production Ready** | Designed for scalability and reliability |
| 🌐 **API Gateway** | Unified interface with WebSocket support |
| 📊 **Monitoring** | Built-in metrics and health checks |
| 🌍 **Web Integration** | Full support for web technologies (HTML, CSS, JS, React) |

</div>

---

## 🚀 **Quick Start**

### Installation

```bash
pip install qyro
```

### Basic Usage

Create a `.qyro` file:

```qyro
>>>schema
{
    "player_x": 0,
    "player_y": 0,
    "score": 0,
    "game_over": false,
    "message": "Hello Qyro"
}

>>>py
import time
from qyro.adapters import QyroMemory
import json

mem = QyroMemory()
while True:
    data = mem.read()
    print(f"Python module sees state: {data}")
    time.sleep(1)

>>>c
#include "qyro.h"
#include <stdio.h>

int main() {
    printf("C module starting...\n");

    // Initialize connection
    if (qyro_init() != QYRO_OK) {
        printf("Failed to initialize\n");
        return 1;
    }

    // Read state
    char* state = qyro_read_state();
    printf("C module read: %s\n", state);
    free(state);

    // Update state
    qyro_write_field("c_counter", "100");

    qyro_cleanup();
    return 0;
}

>>>rs
use qyro_adapter::Qyro;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut qyro = Qyro::new();
    qyro.connect().await?;

    loop {
        let state = qyro.read_state().await?;
        println!("Rust module sees state: {:?}", state);

        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    }
}
```

### Run Your Application

```bash
qyro run main.qyro
```

---

## 🛠️ **Advanced Usage**

### Using the Qyro Runtime Programmatically

```python
from qyro.orchestrator.orchestrator import QyroOrchestrator
from qyro.common.config import QyroConfig

# Create configuration
config = QyroConfig(
    redis_host="localhost",
    redis_port=6379,
    kafka_bootstrap_services="localhost:9092"
)

# Create orchestrator
orchestrator = QyroOrchestrator(
    qyro_file="main.qyro",
    config=config
)

# Start the orchestrator
orchestrator.start()
```

### Animation in Your Applications

```python
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
import time

console = Console()

# Create animated elements
def show_loading(message="Processing"):
    spinner = Spinner("dots", style="green")
    text = Text(message, style="bold blue")
    panel = Panel(spinner, title=text, border_style="blue")
    
    with Live(panel, refresh_per_second=20):
        time.sleep(3)  # Simulate work
    
    console.print("[bold green]Done![/bold green]")

show_loading("Running Qyro Module...")
```

---

## 📦 **Supported Languages**

<div align="center">

| Language | Status | Adapter |
|----------|--------|---------|
| Python 🐍 | ✅ Stable | `qyro.adapters.python` |
| C/C++ 🖥️ | ✅ Stable | `qyro.adapters.c` |
| Rust 🦀 | ✅ Stable | `qyro.adapters.rust` |
| Java ☕ | ✅ Stable | `qyro.adapters.java` |
| Go 🐹 | ⚡ Beta | `qyro.adapters.go` |
| JavaScript 🟨 | ⚡ Beta | `qyro.adapters.javascript` |
| TypeScript 🔵 | ⚡ Beta | `qyro.adapters.typescript` |
| React ⚛️ | ⚡ Beta | `qyro.adapters.react` |

</div>

---

## 📚 **API Reference**

### Gateway API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /state` - Get current application state
- `POST /state` - Update application state
- `WS /ws` - WebSocket endpoint for real-time communication

### Language Adapter API

Each language has its own adapter with consistent APIs:

#### Python
```python
from qyro.adapters.language_adapters.python.python_adapter import QyroModule

qyro = QyroModule("python_module")
qyro.connect()

state = qyro.read_state()  # Read all state
qyro.write_state({"key": "value"})  # Update multiple fields
qyro.update_field("key", "value")  # Update specific field

qyro.disconnect()
```

---

## 🧪 **Examples**

### Simple Counter Application

```qyro
>>>schema
{
    "counter": 0,
    "last_updated": ""
}

>>>py
import time
from qyro.adapters import QyroMemory
import datetime

mem = QyroMemory()
while True:
    data = mem.read()
    counter = data.get("counter", 0)
    new_counter = counter + 1
    
    update = {
        "counter": new_counter,
        "last_updated": str(datetime.datetime.now())
    }
    
    mem.write(update)
    print(f"Counter updated to: {new_counter}")
    time.sleep(2)
```

### Animation Example

```python
from qyro.common.animation import AnimatedConsole
from rich.text import Text

console = AnimatedConsole()

# Animated header
console.animate_ascii("QYRO", font="slant", style="bold cyan")
console.print(Text("Universal Polyglot Runtime", style="bold magenta"))

# Animated progress
console.animate_progress("Initializing modules", 5)
```

---

## 🤝 **Contributing**

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md).

### Development Setup

```bash
# Clone the repository
git clone https://github.com/qyro-dev/qyro.git
cd qyro

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### Made with ❤️ for developers who love to code in multiple languages

[![GitHub stars](https://img.shields.io/github/stars/qyro-dev/qyro?style=social)](https://github.com/qyro-dev/qyro)
[![Twitter Follow](https://img.shields.io/twitter/follow/qyro_dev?style=social)](https://twitter.com/qyro_dev)

</div>