# Qyro VS Code Extension

Syntax highlighting, snippets, and language support for Qyro polyglot files.

## Features

- 🎨 **Syntax Highlighting** for all supported languages:
  - Python
  - JavaScript/TypeScript/React
  - Rust
  - Java
  - Go
  - C/C++

- 📝 **Snippets** for quick service creation:
  - `>>>python` - Python FastAPI service
  - `>>>web` - React frontend
  - `>>>rust` - Rust service
  - `>>>java` - Java service
  - `>>>go` - Go service
  - `>>>c` - C service
  - `qyro-call` - RPC call
  - `qyro-expose` - Expose function

- 🔗 **Embedded Language Support** - Full IntelliSense for embedded languages

## Installation

### From VSIX

1. Download the `.vsix` file from releases
2. In VS Code: `Extensions` → `...` → `Install from VSIX`
3. Select the downloaded file

### Manual Installation

1. Copy this folder to `~/.vscode/extensions/qyro-vscode`
2. Restart VS Code

## Usage

Create a `.qyro` file and start typing:

```qyro
# My Qyro App

>>>python:api [fastapi, uvicorn]
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello!"}

>>>web:frontend [react]
import React from 'react';
function App() {
  return <h1>Hello Qyro!</h1>;
}
export default App;
```

## License

MIT
