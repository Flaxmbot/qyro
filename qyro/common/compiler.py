"""
Nexus Code Compiler
Compiles polyglot code blocks with basic validation and linting.
WARNING: This is NOT a security sandbox - only run trusted code.
"""

import subprocess
import os
import sys
import shutil
import re
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import distutils.dir_util

from .logging import get_logger
from .errors import NexusError, ErrorCode
from .platform import get_platform
from .toolchain_validator import ToolchainValidator, ToolchainStatus

logger = get_logger("nexus.compiler")

# Security note: These patterns were previously used for basic linting but are not effective as a security sandbox.
# The Nexus project assumes trusted code input. For untrusted code, use proper sandboxing (containers, WASM, etc.)
BANNED_C_PATTERNS = []

BANNED_RUST_PATTERNS = []

BANNED_GO_PATTERNS = []


@dataclass
class CompilationResult:
    """Result of a compilation attempt."""
    success: bool
    artifact: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class CompilerConfig:
    """Compiler configuration options."""
    timeout_seconds: int = 60              # Compilation timeout
    max_code_size: int = 1024 * 1024       # Max 1MB code size
    allow_unsafe: bool = False             # Allow unsafe code patterns
    extra_flags: List[str] = None          # Additional compiler flags

    def __post_init__(self):
        if self.extra_flags is None:
            self.extra_flags = []


class CodeLinter:
    """
    Validates code for obvious anti-patterns before compilation.
    NOTE: This is NOT a security sandbox. Only use with trusted code.
    These checks are for basic linting purposes only.
    """

    @staticmethod
    def validate_c(code: str, config: CompilerConfig) -> List[str]:
        """Validate C code, returns list of issues found."""
        issues = []

        if len(code) > config.max_code_size:
            issues.append(f"Code exceeds max size: {len(code)} > {config.max_code_size}")
            return issues

        # Check for dangerous patterns
        is_safe, reason = InputValidator.validate_dangerous_content(code)
        if not is_safe:
            issues.append(f"Dangerous content detected: {reason}")
            return issues

        # Only warn about patterns if they exist, but don't block compilation
        for pattern in BANNED_C_PATTERNS:
            if re.search(pattern, code):
                issues.append(f"Suspicious pattern found (lint warning): {pattern}")

        return issues

    @staticmethod
    def validate_rust(code: str, config: CompilerConfig) -> List[str]:
        """Validate Rust code."""
        issues = []

        if len(code) > config.max_code_size:
            issues.append(f"Code exceeds max size")
            return issues

        # Check for dangerous patterns
        is_safe, reason = InputValidator.validate_dangerous_content(code)
        if not is_safe:
            issues.append(f"Dangerous content detected: {reason}")
            return issues

        for pattern in BANNED_RUST_PATTERNS:
            match = re.search(pattern, code)
            if match:
                if 'unsafe' in pattern and config.allow_unsafe:
                    continue  # Skip unsafe warning if allowed
                issues.append(f"Suspicious pattern found (lint warning): {pattern}")

        return issues

    @staticmethod
    def validate_go(code: str, config: CompilerConfig) -> List[str]:
        """Validate Go code."""
        issues = []

        if len(code) > config.max_code_size:
            issues.append(f"Code exceeds max size")
            return issues

        # Check for dangerous patterns
        is_safe, reason = InputValidator.validate_dangerous_content(code)
        if not is_safe:
            issues.append(f"Dangerous content detected: {reason}")
            return issues

        for pattern in BANNED_GO_PATTERNS:
            if re.search(pattern, code):
                issues.append(f"Suspicious pattern found (lint warning): {pattern}")

        return issues


import hashlib
import pickle
from .validation import validate_input, InputValidator, ValidationError

class NexusCompiler:
    """
    Compiler for polyglot code blocks with security validation.

    NOTE: This compiler provides basic input validation but should be used
    with the secure sandbox system for untrusted code.

    Features:
    - Code compilation and linking
    - Cross-platform execution
    - Compilation timeouts
    - Size limits
    - Input validation and sanitization

    Cross-Platform Features:
    - Platform abstraction for paths and executables
    - Pre-flight toolchain validation
    - Graceful degradation when toolchains are missing
    """

    def __init__(self, config: CompilerConfig = None, skip_missing: bool = True):
        self.config = config or CompilerConfig()
        self.validator = CodeLinter()
        self.platform = get_platform()
        self.toolchain_validator = ToolchainValidator()
        self.skip_missing = skip_missing
        self.warnings: List[str] = []

        # Run toolchain validation on initialization
        self.toolchain_validator.check_all()

        # Initialize incremental compilation cache
        self.cache_dir = ".nexus_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, "build_cache.pkl")
        self.build_cache = self._load_cache()

    def compile(self, blocks: Dict[str, List[str]], skip_missing: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Compile all code blocks with graceful degradation.

        Args:
            blocks: Dictionary mapping language names to code blocks
            skip_missing: Whether to skip compilation for missing toolchains (default: from __init__)

        Returns:
            List of compiled artifacts
        """
        if skip_missing is not None:
            self.skip_missing = skip_missing

        artifacts = []
        self.warnings = []

        # C blocks
        for i, code in enumerate(blocks.get('c', [])):
            if not self._check_toolchain_available('c'):
                if self.skip_missing:
                    self.warnings.append(f"Skipping C module {i}: C compiler not available")
                    continue
                else:
                    print(f"[NEXUS] ERROR: C compiler not available")
                    return artifacts

            # Check if we have a cached version
            if self._is_up_to_date('c', i, code):
                cached_artifact = self.build_cache[f"c_{i}"]['artifact']
                artifacts.append(cached_artifact)
                print(f"[NEXUS] Using cached C module {i}")
                continue

            result = self._compile_c(code, i)
            if result.success:
                artifacts.append(result.artifact)
                # Update cache with new artifact
                self._update_cache('c', i, code, result.artifact)
            for warning in result.warnings:
                self.warnings.append(f"C Warning: {warning}")
                print(f"[NEXUS] C Warning: {warning}")

        # Rust blocks
        for i, code in enumerate(blocks.get('rs', [])):
            if not self._check_toolchain_available('rust'):
                if self.skip_missing:
                    self.warnings.append(f"Skipping Rust module {i}: Rust toolchain not available")
                    continue
                else:
                    print(f"[NEXUS] ERROR: Rust toolchain not available")
                    return artifacts

            # Check if we have a cached version
            if self._is_up_to_date('rs', i, code):
                cached_artifact = self.build_cache[f"rs_{i}"]['artifact']
                artifacts.append(cached_artifact)
                print(f"[NEXUS] Using cached Rust module {i}")
                continue

            result = self._compile_rust(code, i)
            if result.success:
                artifacts.append(result.artifact)
                # Update cache with new artifact
                self._update_cache('rs', i, code, result.artifact)
            elif result.error:
                self.warnings.append(f"Rust module {i}: {result.error}")

        # Java blocks
        for i, code in enumerate(blocks.get('java', [])):
            if not self._check_toolchain_available('java'):
                if self.skip_missing:
                    self.warnings.append(f"Skipping Java module {i}: Java compiler not available")
                    continue
                else:
                    print(f"[NEXUS] ERROR: Java compiler not available")
                    return artifacts

            # Check if we have a cached version
            if self._is_up_to_date('java', i, code):
                cached_artifact = self.build_cache[f"java_{i}"]['artifact']
                artifacts.append(cached_artifact)
                print(f"[NEXUS] Using cached Java module {i}")
                continue

            result = self._compile_java(code, i)
            if result.success:
                artifacts.append(result.artifact)
                # Update cache with new artifact
                self._update_cache('java', i, code, result.artifact)
            elif result.error:
                self.warnings.append(f"Java module {i}: {result.error}")

        # Go blocks
        for i, code in enumerate(blocks.get('go', [])):
            if not self._check_toolchain_available('go'):
                if self.skip_missing:
                    self.warnings.append(f"Skipping Go module {i}: Go compiler not available")
                    continue
                else:
                    print(f"[NEXUS] ERROR: Go compiler not available")
                    return artifacts

            # Check if we have a cached version
            if self._is_up_to_date('go', i, code):
                cached_artifact = self.build_cache[f"go_{i}"]['artifact']
                artifacts.append(cached_artifact)
                print(f"[NEXUS] Using cached Go module {i}")
                continue

            result = self._compile_go(code, i)
            if result.success:
                artifacts.append(result.artifact)
                # Update cache with new artifact
                self._update_cache('go', i, code, result.artifact)
            elif result.error:
                self.warnings.append(f"Go module {i}: {result.error}")

        # TypeScript blocks (no compilation, just save)
        for i, code in enumerate(blocks.get('ts', [])):
            if not self._check_toolchain_available('typescript'):
                if self.skip_missing:
                    self.warnings.append(f"Skipping TypeScript module {i}: Node.js not available")
                    continue
                else:
                    print(f"[NEXUS] ERROR: Node.js not available for TypeScript")
                    return artifacts

            # Check if we have a cached version
            if self._is_up_to_date('ts', i, code):
                cached_artifact = self.build_cache[f"ts_{i}"]['artifact']
                artifacts.append(cached_artifact)
                print(f"[NEXUS] Using cached TypeScript module {i}")
                continue

            filename = f"nexus_module_ts_{i}.ts"
            with open(filename, "w", encoding='utf-8') as f:
                f.write(code)
            artifact = {'type': 'ts', 'src': filename}
            artifacts.append(artifact)
            # Update cache with new artifact
            self._update_cache('ts', i, code, artifact)

        # Python blocks (no compilation, just save)
        for i, code in enumerate(blocks.get('py', [])):
            if not self._check_toolchain_available('python'):
                if self.skip_missing:
                    self.warnings.append(f"Skipping Python module {i}: Python not available")
                    continue
                else:
                    print(f"[NEXUS] ERROR: Python not available")
                    return artifacts

            # Check if we have a cached version
            if self._is_up_to_date('py', i, code):
                cached_artifact = self.build_cache[f"py_{i}"]['artifact']
                artifacts.append(cached_artifact)
                print(f"[NEXUS] Using cached Python module {i}")
                continue

            filename = f"nexus_module_py_{i}.py"
            with open(filename, "w", encoding='utf-8') as f:
                f.write(code)
            artifact = {'type': 'py', 'src': filename}
            artifacts.append(artifact)
            # Update cache with new artifact
            self._update_cache('py', i, code, artifact)

        # Web blocks
        for i, code in enumerate(blocks.get('web', [])):
            if not self._check_toolchain_available('python'):
                if self.skip_missing:
                    self.warnings.append(f"Skipping Web module {i}: Python not available")
                    continue
                else:
                    print(f"[NEXUS] ERROR: Python not available for Web modules")
                    return artifacts

            # Check if we have a cached version
            if self._is_up_to_date('web', i, code):
                cached_artifact = self.build_cache[f"web_{i}"]['artifact']
                artifacts.append(cached_artifact)
                print(f"[NEXUS] Using cached Web module {i}")
                continue

            filename = f"nexus_web_{i}.py"
            with open(filename, "w", encoding='utf-8') as f:
                f.write(code)
            artifact = {'type': 'web', 'src': filename}
            artifacts.append(artifact)
            # Update cache with new artifact
            self._update_cache('web', i, code, artifact)

        # React/Next.js blocks
        if blocks.get('react'):
            if self._check_toolchain_available('typescript'):
                self._compile_frontend(blocks['react'], 'react', artifacts)
            elif self.skip_missing:
                self.warnings.append("Skipping React modules: Node.js not available")
            else:
                print(f"[NEXUS] ERROR: Node.js not available for React modules")
                return artifacts

        if blocks.get('nextjs'):
            if self._check_toolchain_available('typescript'):
                self._compile_frontend(blocks['nextjs'], 'nextjs', artifacts)
            elif self.skip_missing:
                self.warnings.append("Skipping Next.js modules: Node.js not available")
            else:
                print(f"[NEXUS] ERROR: Node.js not available for Next.js modules")
                return artifacts

        # Print warnings
        if self.warnings:
            print(f"[NEXUS] Warnings during compilation:")
            for warning in self.warnings:
                print(f"[NEXUS]   - {warning}")

        # Save the cache after compilation
        self._save_cache()

        print(f"[NEXUS] Compilation complete: {len(artifacts)} modules compiled.")
        logger.info("compilation_complete", count=len(artifacts), warnings=len(self.warnings))
        return artifacts

    def _load_cache(self) -> Dict[str, Any]:
        """Load the build cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                # If cache is corrupted, start fresh
                return {}
        return {}

    def _save_cache(self):
        """Save the build cache to disk."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.build_cache, f)
        except Exception as e:
            logger.warning("cache_save_failed", error=str(e))

    def _get_file_hash(self, content: str) -> str:
        """Generate a hash for the file content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _is_up_to_date(self, lang: str, index: int, content: str) -> bool:
        """Check if the compiled artifact is up to date."""
        cache_key = f"{lang}_{index}"
        if cache_key not in self.build_cache:
            return False

        cached_hash = self.build_cache[cache_key].get('hash')
        current_hash = self._get_file_hash(content)

        return cached_hash == current_hash

    def _update_cache(self, lang: str, index: int, content: str, artifact: Dict[str, Any]):
        """Update the build cache with new information."""
        cache_key = f"{lang}_{index}"
        self.build_cache[cache_key] = {
            'hash': self._get_file_hash(content),
            'artifact': artifact,
            'timestamp': time.time()
        }

    def _check_toolchain_available(self, language: str) -> bool:
        """
        Check if a toolchain is available for a language.

        Args:
            language: Language name (c, java, rust, go, typescript, python)

        Returns:
            True if toolchain is available, False otherwise
        """
        return self.toolchain_validator.is_language_available(language)

    def _compile_c(self, code: str, index: int) -> CompilationResult:
        """Compile C code with validation and platform abstraction."""
        # Validate first
        issues = self.validator.validate_c(code, self.config)
        if issues:
            logger.warning("c_validation_failed", issues=issues)
            return CompilationResult(
                success=False,
                error=f"Validation failed: {issues}",
                warnings=issues
            )

        # Sanitize the code before compilation
        try:
            from .validation import InputSanitizer
            sanitized_code = InputSanitizer.sanitize_for_shell(code)
        except ImportError:
            sanitized_code = code  # Fallback if sanitizer not available

        filename = f"nexus_module_c_{index}.c"
        exe_name = self.platform.get_executable_name(f"nexus_module_c_{index}")

        # Validate filename to prevent path traversal
        if '..' in filename or filename.startswith('/') or ':' in filename:
            return CompilationResult(
                success=False,
                error="Invalid filename detected (potential path traversal)"
            )

        # Add includes
        full_code = '#include "nexus_core/adapters/nexus.h"\n'
        if os.path.exists("nexus_generated/nexus_types.h"):
            full_code += '#include "nexus_generated/nexus_types.h"\n'
        full_code += sanitized_code

        # Write to a temporary directory to prevent file system pollution
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_filename = os.path.join(temp_dir, os.path.basename(filename))
            temp_exe_name = os.path.join(temp_dir, os.path.basename(exe_name))

            with open(temp_filename, "w", encoding='utf-8') as f:
                f.write(full_code)

            # Determine which C compiler to use (gcc or clang)
            compiler = 'gcc'
            if not self.platform.which('gcc') and self.platform.which('clang'):
                compiler = 'clang'

            # Compile with security flags and timeout
            cmd = [
                compiler,
                "-o", temp_exe_name,
                temp_filename,
                "-I.",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-fstack-protector-strong",  # Stack protection
                "-D_FORTIFY_SOURCE=2",      # Additional protections
                "-O2"                       # Optimization with security
            ]
            cmd.extend(self.config.extra_flags)

            try:
                print(f"[NEXUS] Compiling {filename} with {compiler}...")
                returncode, stdout, stderr = self.platform.run_command(
                    cmd,
                    timeout=self.config.timeout_seconds
                )

                if returncode != 0:
                    print(f"[NEXUS] C Compilation Failed:\n{stderr}")
                    logger.error("c_compilation_failed", stderr=stderr)
                    return CompilationResult(
                        success=False,
                        error=stderr
                    )

                # Move the compiled binary to the current directory
                import shutil
                shutil.move(temp_exe_name, exe_name)

                logger.info("c_compiled", filename=filename, exe=exe_name)
                return CompilationResult(
                    success=True,
                    artifact={'type': 'c', 'bin': exe_name}
                )

            except subprocess.TimeoutExpired:
                logger.error("c_compilation_timeout", filename=filename)
                return CompilationResult(
                    success=False,
                    error="Compilation timed out"
                )
            except Exception as e:
                print(f"[NEXUS] C Compiler Error: {e}")
                logger.error("c_compilation_error", error=str(e))
                return CompilationResult(success=False, error=str(e))

    def _compile_rust(self, code: str, index: int) -> CompilationResult:
        """Compile Rust code with validation and robust error handling."""
        issues = self.validator.validate_rust(code, self.config)
        if issues:
            logger.warning("rust_validation_failed", issues=issues)
            return CompilationResult(success=False, error=f"Validation: {issues}")

        project_dir = f"nexus_rust_project_{index}"
        exe_name = self.platform.get_executable_name(f"nexus_module_rs_{index}")

        # Pre-flight check: Verify cargo is available
        returncode, stdout, stderr = self.platform.run_command(
            ["cargo", "--version"],
            timeout=5
        )

        if returncode != 0:
            error_msg = (
                "Rust toolchain not found. Cargo is required for Rust compilation.\n"
                "Please install Rust from https://rustup.rs/ or run:\n"
                "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh  (Linux/Mac)\n"
                "  Or download from https://rustup.rs/  (Windows)"
            )
            print(f"[NEXUS] {error_msg}")
            logger.warning("rust_toolchain_not_found")
            return CompilationResult(success=False, error=error_msg)

        logger.info("cargo_available", version=stdout.strip())

        # Pre-flight check: Verify nexus_adapter path exists
        adapter_path = os.path.join("nexus_core", "adapters", "rust")
        if not os.path.exists(adapter_path):
            error_msg = (
                f"Rust adapter not found at: {adapter_path}\n"
                f"Expected path relative to project directory: {project_dir}\n"
                f"Please ensure nexus_core/adapters/rust exists in the project."
            )
            print(f"[NEXUS] {error_msg}")
            logger.warning("rust_adapter_not_found", path=adapter_path)
            return CompilationResult(success=False, error=error_msg)

        # Create Rust project structure
        try:
            os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
        except Exception as e:
            error_msg = f"Failed to create Rust project directory: {str(e)}"
            print(f"[NEXUS] {error_msg}")
            logger.error("rust_project_creation_failed", error=str(e))
            return CompilationResult(success=False, error=error_msg)

        # Write Cargo.toml with corrected path
        cargo_toml_path = os.path.join(project_dir, "Cargo.toml")
        try:
            # Copy the nexus_adapter to the temporary project directory to make the path work
            temp_adapter_path = os.path.join(project_dir, "nexus_core", "adapters", "rust")
            os.makedirs(temp_adapter_path, exist_ok=True)

            # Copy all files from the original adapter to the temp location
            original_adapter_path = os.path.join("nexus_core", "adapters", "rust")
            if os.path.exists(original_adapter_path):
                # Use shutil.copytree to copy the entire directory
                if os.path.exists(temp_adapter_path):
                    shutil.rmtree(temp_adapter_path)
                shutil.copytree(original_adapter_path, temp_adapter_path)
            else:
                error_msg = f"Original adapter path does not exist: {original_adapter_path}"
                print(f"[NEXUS] {error_msg}")
                logger.error("adapter_path_not_found", path=original_adapter_path)
                return CompilationResult(success=False, error=error_msg)

            with open(cargo_toml_path, "w", encoding='utf-8') as f:
                f.write(f"""[package]
name = "nexus_module_rs_{index}"
version = "0.1.0"
edition = "2021"

[dependencies]
memmap2 = "0.9"
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
nexus_adapter = {{ path = "nexus_core/adapters/rust" }}
""")
            logger.info("cargo_toml_written", path=cargo_toml_path)
        except Exception as e:
            error_msg = f"Failed to write Cargo.toml: {str(e)}"
            print(f"[NEXUS] {error_msg}")
            logger.error("cargo_toml_write_failed", error=str(e))
            return CompilationResult(success=False, error=error_msg)

        # Handle generated types
        try:
            os.makedirs(os.path.join(project_dir, "src/nexus_generated"), exist_ok=True)
            if os.path.exists("nexus_generated/nexus_types.rs"):
                shutil.copy(
                    "nexus_generated/nexus_types.rs",
                    os.path.join(project_dir, "src/nexus_generated/nexus_types.rs")
                )
                with open(os.path.join(project_dir, "src/nexus_generated/mod.rs"), "w", encoding='utf-8') as f:
                    f.write("pub mod nexus_types;")
        except Exception as e:
            logger.warning("generated_types_copy_failed", error=str(e))
            # Non-fatal, continue with compilation

        # Write main.rs
        main_rs_path = os.path.join(project_dir, "src/main.rs")
        try:
            full_code = 'mod nexus_generated;\nuse nexus_adapter;\n' + code
            with open(main_rs_path, "w", encoding='utf-8') as f:
                f.write(full_code)
            logger.info("main_rs_written", path=main_rs_path)
        except Exception as e:
            error_msg = f"Failed to write main.rs: {str(e)}"
            print(f"[NEXUS] {error_msg}")
            logger.error("main_rs_write_failed", error=str(e))
            return CompilationResult(success=False, error=error_msg)

        # Build with cargo
        try:
            print(f"[NEXUS] Building Rust project {project_dir}...")
            logger.info("rust_build_started", project=project_dir)

            result = subprocess.run(
                ["cargo", "build", "--release"],
                cwd=project_dir,
                capture_output=True,
                timeout=self.config.timeout_seconds * 2,  # Rust takes longer
                text=True,
                encoding='utf-8'
            )

            if result.returncode != 0:
                stderr_output = result.stderr if result.stderr else "No error output"
                stdout_output = result.stdout if result.stdout else ""

                # Check for common Windows build tool issues
                if "link.exe" in stderr_output or "linker" in stderr_output.lower():
                    error_msg = (
                        "Rust compilation failed: Visual C++ build tools not found.\n"
                        "On Windows, Rust requires Microsoft Visual C++ Build Tools.\n"
                        "Please install from: https://visualstudio.microsoft.com/visual-cpp-build-tools/\n"
                        "Select 'Desktop development with C++' during installation.\n\n"
                        f"Error details:\n{stderr_output}"
                    )
                elif "nexus_adapter" in stderr_output:
                    error_msg = (
                        f"Rust compilation failed: Could not find nexus_adapter dependency.\n"
                        f"Expected path: {adapter_path}\n"
                        f"Please ensure the nexus_core/adapters/rust directory exists.\n\n"
                        f"Error details:\n{stderr_output}"
                    )
                else:
                    error_msg = (
                        f"Rust compilation failed.\n"
                        f"Error details:\n{stderr_output}\n"
                        f"Output:\n{stdout_output}"
                    )

                print(f"[NEXUS] {error_msg}")
                logger.error("rust_compilation_failed",
                            returncode=result.returncode,
                            stderr=stderr_output,
                            stdout=stdout_output)
                return CompilationResult(success=False, error=error_msg)

            # Locate and copy the compiled binary
            bin_path = os.path.join(project_dir, "target", "release", f"nexus_module_rs_{index}.exe")
            if os.path.exists(bin_path):
                shutil.copy(bin_path, exe_name)
                logger.info("rust_binary_copied", src=bin_path, dst=exe_name)
            else:
                # Try without .exe extension (Linux/Mac)
                bin_path_no_ext = os.path.join(project_dir, "target", "release", f"nexus_module_rs_{index}")
                if os.path.exists(bin_path_no_ext):
                    shutil.copy(bin_path_no_ext, exe_name)
                    logger.info("rust_binary_copied", src=bin_path_no_ext, dst=exe_name)
                else:
                    error_msg = (
                        f"Rust compilation succeeded but binary not found.\n"
                        f"Expected: {bin_path} or {bin_path_no_ext}\n"
                        f"Build output:\n{result.stdout}"
                    )
                    print(f"[NEXUS] {error_msg}")
                    logger.error("rust_binary_not_found",
                                expected1=bin_path,
                                expected2=bin_path_no_ext)
                    return CompilationResult(success=False, error=error_msg)

            logger.info("rust_compilation_succeeded", project=project_dir, exe=exe_name)
            return CompilationResult(
                success=True,
                artifact={'type': 'rs', 'bin': exe_name}
            )

        except subprocess.TimeoutExpired:
            error_msg = (
                f"Rust compilation timed out after {self.config.timeout_seconds * 2} seconds.\n"
                "The project may be too large or there may be dependency issues.\n"
                "Try increasing timeout_seconds in CompilerConfig."
            )
            print(f"[NEXUS] {error_msg}")
            logger.error("rust_compilation_timeout",
                        timeout=self.config.timeout_seconds * 2,
                        project=project_dir)
            return CompilationResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during Rust compilation: {str(e)}"
            print(f"[NEXUS] {error_msg}")
            logger.error("rust_compilation_error", error=str(e), project=project_dir)
            return CompilationResult(success=False, error=error_msg)

    def _compile_java(self, code: str, index: int) -> CompilationResult:
        """Compile Java code with wrapper support and platform abstraction."""
        import re
        class_match = re.search(r'public\s+class\s+(\w+)', code)
        class_name = class_match.group(1) if class_match else f"NexusModule_{index}"

        filename = f"{class_name}.java"
        full_code = 'import nexus.Nexus;\nimport nexus.GlobalState;\n' + code

        with open(filename, "w", encoding='utf-8') as f:
            f.write(full_code)

        # Setup classpath
        os.makedirs("nexus_build/nexus", exist_ok=True)

        # Copy Nexus adapter
        if os.path.exists("nexus_core/adapters/Nexus.java"):
            shutil.copy("nexus_core/adapters/Nexus.java", "nexus_build/nexus/Nexus.java")
        if os.path.exists("nexus_generated/GlobalState.java"):
            shutil.copy("nexus_generated/GlobalState.java", "nexus_build/nexus/GlobalState.java")

        # Copy NexusModuleRunner wrapper
        if os.path.exists("nexus_core/adapters/NexusModuleRunner.java"):
            shutil.copy("nexus_core/adapters/NexusModuleRunner.java", "nexus_build/nexus/NexusModuleRunner.java")

        try:
            # Compile Nexus adapter first
            self.platform.run_command(
                ["javac", "nexus_build/nexus/Nexus.java"],
                timeout=self.config.timeout_seconds
            )

            # Compile NexusModuleRunner wrapper
            self.platform.run_command(
                ["javac", "-cp", "nexus_build", "nexus_build/nexus/NexusModuleRunner.java"],
                timeout=self.config.timeout_seconds
            )

            # Check if external libraries exist in lib directory
            lib_dir = "lib"
            classpath_sep = ';' if self.platform.is_windows() else ':'

            # Build classpath
            classpath = f"nexus_build{classpath_sep}."
            if os.path.exists(lib_dir):
                for jar_file in os.listdir(lib_dir):
                    if jar_file.endswith('.jar'):
                        classpath += f"{classpath_sep}{lib_dir}/{jar_file}"

            # Compile user code with external libraries if available
            returncode, stdout, stderr = self.platform.run_command(
                ["javac", "-cp", classpath, filename],
                timeout=self.config.timeout_seconds
            )

            if returncode != 0:
                print(f"[NEXUS] Java Compilation Failed:\n{stderr}")
                logger.error("java_compilation_failed", stderr=stderr)
                return CompilationResult(success=False, error=stderr)

            # Platform-specific classpath separator
            classpath_sep = ';' if self.platform.is_windows() else ':'

            # Return wrapper class as the executable, with user class as argument
            return CompilationResult(
                success=True,
                artifact={
                    'type': 'java',
                    'class': 'nexus.NexusModuleRunner',  # Wrapper class
                    'user_class': class_name,  # User's actual class
                    'cp': f'nexus_build{classpath_sep}.'
                }
            )

        except subprocess.TimeoutExpired:
            return CompilationResult(success=False, error="Java compilation timed out")
        except Exception as e:
            print(f"[NEXUS] Java Compiler Error: {e}")
            return CompilationResult(success=False, error=str(e))

    def _compile_go(self, code: str, index: int) -> CompilationResult:
        """Compile Go code with validation and platform abstraction."""
        issues = self.validator.validate_go(code, self.config)
        if issues:
            return CompilationResult(success=False, error=f"Validation: {issues}")

        filename = f"nexus_module_go_{index}.go"
        exe_name = self.platform.get_executable_name(f"nexus_module_go_{index}")

        with open(filename, "w", encoding='utf-8') as f:
            f.write(code)

        try:
            print(f"[NEXUS] Building Go module {filename}...")
            returncode, stdout, stderr = self.platform.run_command(
                ["go", "build", "-o", exe_name, filename],
                timeout=self.config.timeout_seconds
            )

            if returncode != 0:
                print(f"[NEXUS] Go Compilation Failed:\n{stderr}")
                logger.error("go_compilation_failed", stderr=stderr)
                return CompilationResult(success=False, error=stderr)

            return CompilationResult(
                success=True,
                artifact={'type': 'go', 'bin': exe_name}
            )

        except subprocess.TimeoutExpired:
            return CompilationResult(success=False, error="Go compilation timed out")
        except Exception as e:
            print(f"[NEXUS] Go Compiler Error: {e}")
            return CompilationResult(success=False, error=str(e))

    def _compile_frontend(self, blocks: List[str], framework: str, artifacts: List[Dict]):
        """Compile React/Next.js blocks."""
        try:
            from .frontend import FrontendCompiler, FrontendConfig
            config = FrontendConfig(framework=framework)
            fc = FrontendCompiler('nexus_frontend')

            for i, code in enumerate(blocks):
                if framework == 'react':
                    result = fc.compile_react(code, config)
                else:
                    result = fc.compile_nextjs(code, config)
                artifacts.append(result)
                print(f"[NEXUS] {framework.title()} component generated")

        except ImportError:
            logger.warning("frontend_compiler_not_found")
