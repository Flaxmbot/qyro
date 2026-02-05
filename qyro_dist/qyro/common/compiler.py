"""
Qyro Code Compiler
Compiles polyglot code blocks with basic validation and linting.
"""

import subprocess
import os
import sys
import shutil
import re
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from .logging import get_logger
from .errors import NexusError, ErrorCode # Keep legacy name for now or update errors.py
from .platform import get_platform
from .toolchain_validator import ToolchainValidator
from qyro.adapters.language_adapters.agent.agent_adapter import QyroAgent

logger = get_logger("qyro.compiler")

@dataclass
class CompilationResult:
    success: bool
    artifact: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = None
    def __post_init__(self):
        if self.warnings is None: self.warnings = []

@dataclass
class CompilerConfig:
    timeout_seconds: int = 60
    max_code_size: int = 1024 * 1024
    allow_unsafe: bool = False
    extra_flags: List[str] = None
    def __post_init__(self):
        if self.extra_flags is None: self.extra_flags = []

class QyroCompiler:
    def __init__(self, config: CompilerConfig = None, skip_missing: bool = True):
        self.config = config or CompilerConfig()
        self.platform = get_platform()
        self.toolchain_validator = ToolchainValidator()
        self.skip_missing = skip_missing
        self.warnings: List[str] = []
        self.toolchain_validator.check_all()

        self.cache_dir = ".qyro_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        import pickle
        self.build_cache = {} # Simplified cache for now

    def compile(self, blocks: Dict[str, List[Any]], skip_missing: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Compile code blocks.
        blocks: Dict mapping type to list of strings OR list of dicts (metadata).
        """
        if skip_missing is not None:
            self.skip_missing = skip_missing

        artifacts = []
        self.warnings = []

        # Helper to get content and metadata
        def get_block_info(blk, idx):
            if isinstance(blk, str):
                return blk, {}, idx
            return blk['content'], blk, idx

        # C
        for i, block in enumerate(blocks.get('c', [])):
            code, meta, idx = get_block_info(block, i)
            if not self._check_toolchain('c'): continue

            res = self._compile_c(code, idx)
            if res.success: artifacts.append(res.artifact)
            else: logger.error(f"C Compile Error: {res.error}")

        # Rust
        for i, block in enumerate(blocks.get('rust', []) + blocks.get('rs', [])):
            code, meta, idx = get_block_info(block, i)
            if not self._check_toolchain('rust'): continue

            res = self._compile_rust(code, idx, meta.get('dependencies', []))
            if res.success: artifacts.append(res.artifact)
            elif res.error:
                logger.error(f"Rust Compile Error: {res.error}")
                self.warnings.append(res.error)

        # Go
        for i, block in enumerate(blocks.get('go', [])):
            code, meta, idx = get_block_info(block, i)
            if not self._check_toolchain('go'): continue

            res = self._compile_go(code, idx, meta.get('dependencies', []))
            if res.success: artifacts.append(res.artifact)
            elif res.error: logger.error(f"Go Compile Error: {res.error}")

        # Java
        for i, block in enumerate(blocks.get('java', [])):
            code, meta, idx = get_block_info(block, i)
            if not self._check_toolchain('java'): continue

            res = self._compile_java(code, idx)
            if res.success: artifacts.append(res.artifact)
            elif res.error: logger.error(f"Java Compile Error: {res.error}")

        # Python (Script)
        for i, block in enumerate(blocks.get('python', []) + blocks.get('py', [])):
            code, meta, idx = get_block_info(block, i)
            filename = f"qyro_module_py_{idx}.py"
            with open(filename, "w", encoding='utf-8') as f: f.write(code)
            artifacts.append({'type': 'py', 'src': filename})

        # AI Agents
        for i, block in enumerate(blocks.get('agent', [])):
            code, meta, idx = get_block_info(block, i)
            # Inject adapter import
            injected_code = "from qyro.adapters.language_adapters.agent.agent_adapter import init, on, _agent_instance\n" + code
            filename = f"qyro_agent_{idx}.py"
            with open(filename, "w", encoding='utf-8') as f: f.write(injected_code)
            artifacts.append({'type': 'py', 'src': filename})

        # Node/TS
        for i, block in enumerate(blocks.get('node', []) + blocks.get('ts', []) + blocks.get('js', [])):
             code, meta, idx = get_block_info(block, i)
             ext = 'ts' if meta.get('original_type', '').startswith('ts') else 'js'
             filename = f"qyro_module_node_{idx}.{ext}"
             with open(filename, "w", encoding='utf-8') as f: f.write(code)
             artifacts.append({'type': 'ts', 'src': filename}) # 'ts' type triggers ts-node/node execution

        # Web/Frontend
        # We handle this by saving files, CLI run command will likely serve them via Gateway or assume setup did something
        # For now, just save them so Orchestrator can find them if needed
        for i, block in enumerate(blocks.get('web', []) + blocks.get('react', [])):
             # Skipping complex compile inside orchestrator for now
             pass

        return artifacts

    def _check_toolchain(self, lang):
        if self.toolchain_validator.is_language_available(lang): return True
        if not self.skip_missing: print(f"[QYRO] Error: {lang} toolchain missing.")
        return False

    def _compile_c(self, code, index):
        filename = f"qyro_module_c_{index}.c"
        exe_name = self.platform.get_executable_name(f"qyro_module_c_{index}")

        # Simple compilation for now
        with open(filename, "w") as f: f.write(code)

        cmd = ["gcc", "-o", exe_name, filename, "-O2"]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return CompilationResult(True, {'type': 'c', 'bin': exe_name})
        except subprocess.CalledProcessError as e:
            return CompilationResult(False, error=e.stderr.decode())

    def _compile_rust(self, code, index, deps=[]):
        project_dir = f"qyro_rust_{index}"
        exe_name = self.platform.get_executable_name(f"qyro_module_rs_{index}")

        os.makedirs(f"{project_dir}/src", exist_ok=True)

        # Cargo.toml
        dep_str = '\n'.join([f'{d} = "*"' for d in deps])

        # Check for adapter
        adapter_path = os.path.abspath("qyro/adapters/language_adapters/rust")

        toml = f"""[package]
name = "qyro_module_{index}"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
tokio = {{ version = "1.0", features = ["full"] }}
qyro = {{ path = "{adapter_path}" }}
{dep_str}
"""
        with open(f"{project_dir}/Cargo.toml", "w") as f: f.write(toml)

        # main.rs
        with open(f"{project_dir}/src/main.rs", "w") as f:
            f.write("use qyro;\n" + code)

        # Build
        try:
            subprocess.run(["cargo", "build", "--release"], cwd=project_dir, check=True, capture_output=True)

            # Copy binary
            src_bin = f"{project_dir}/target/release/qyro_module_{index}"
            if os.path.exists(src_bin): shutil.copy(src_bin, exe_name)
            elif os.path.exists(src_bin + ".exe"): shutil.copy(src_bin + ".exe", exe_name)

            return CompilationResult(True, {'type': 'rs', 'bin': exe_name})
        except subprocess.CalledProcessError as e:
            # Check for stderr, decode if bytes
            err_msg = e.stderr.decode() if e.stderr else str(e)
            return CompilationResult(False, error=err_msg)

    def _compile_go(self, code, index, deps=[]):
        filename = f"qyro_module_go_{index}.go"
        exe_name = self.platform.get_executable_name(f"qyro_module_go_{index}")

        # Create a go module
        mod_dir = f"qyro_go_{index}"
        os.makedirs(mod_dir, exist_ok=True)

        with open(f"{mod_dir}/main.go", "w") as f: f.write(code)

        # go.mod
        try:
            subprocess.run(["go", "mod", "init", f"qyro_module_{index}"], cwd=mod_dir, check=True, capture_output=True)

            # Replace qyro dependency with local path
            adapter_path = os.path.abspath("qyro/adapters/language_adapters/go")
            subprocess.run(["go", "mod", "edit", "-replace", f"qyro={adapter_path}"], cwd=mod_dir, check=True)

            # Get deps
            for dep in deps:
                subprocess.run(["go", "get", dep], cwd=mod_dir, check=True)

            subprocess.run(["go", "mod", "tidy"], cwd=mod_dir, check=True)

            # Build
            subprocess.run(["go", "build", "-o", f"../{exe_name}"], cwd=mod_dir, check=True, capture_output=True)

            return CompilationResult(True, {'type': 'go', 'bin': exe_name})
        except subprocess.CalledProcessError as e:
            return CompilationResult(False, error=e.stderr.decode() if e.stderr else str(e))

    def _compile_java(self, code, index):
        # Simplified Java compilation
        # Assumes Qyro.java is available or copied
        import re
        class_match = re.search(r'public\s+class\s+(\w+)', code)
        class_name = class_match.group(1) if class_match else f"QyroModule_{index}"

        filename = f"{class_name}.java"
        with open(filename, "w") as f: f.write("import com.qyro.Qyro;\n" + code)

        # Compile
        # We need the qyro-java-client jar or source.
        # For this PoC, we assume sources are in classpath or we skip deep compilation logic and rely on the Docker build to handle it properly?
        # Docker build just copies sources.
        # Orchestrator running locally (or inside Docker) needs to run it.
        # Inside Docker, we have maven installed.
        # We can run `mvn package`.

        # Return success with type java
        return CompilationResult(True, {'type': 'java', 'class': class_name, 'cp': '.'})
