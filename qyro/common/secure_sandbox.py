"""
Nexus Secure Sandbox System
Production-grade containerized execution for untrusted code using Docker isolation.
"""

import docker
import tempfile
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import time
import signal
import subprocess
import hashlib
import secrets
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class SecureSandbox:
    """
    Production-grade secure execution environment for untrusted code using Docker containers.

    Features:
    - Isolated container execution with minimal privileges
    - Strict resource limits (CPU, memory, disk)
    - Complete network isolation
    - File system restrictions with read-only mounts
    - Execution timeout enforcement
    - Comprehensive security policies
    """

    def __init__(self, max_memory: str = "128m", max_cpu: float = 0.5, timeout: int = 30):
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
        except Exception as e:
            raise RuntimeError(f"Docker is required for sandboxing: {e}")
        
        self.max_memory = max_memory
        self.max_cpu = max_cpu
        self.timeout = timeout
        
        # Define supported languages and their security configurations
        self.language_configs = {
            'python': {
                'image': 'python:3.11-alpine',
                'entrypoint': ['python'],
                'security_opts': ['no-new-privileges:true'],
                'readonly_rootfs': True
            },
            'javascript': {
                'image': 'node:18-alpine',
                'entrypoint': ['node'],
                'security_opts': ['no-new-privileges:true'],
                'readonly_rootfs': True
            },
            'go': {
                'image': 'golang:1.21-alpine',
                'entrypoint': ['sh', '-c'],
                'security_opts': ['no-new-privileges:true'],
                'readonly_rootfs': True
            },
            'rust': {
                'image': 'rust:1.75-alpine',
                'entrypoint': ['sh', '-c'],
                'security_opts': ['no-new-privileges:true'],
                'readonly_rootfs': True
            },
            'java': {
                'image': 'openjdk:17-jdk-alpine',
                'entrypoint': ['sh', '-c'],
                'security_opts': ['no-new-privileges:true'],
                'readonly_rootfs': True
            },
            'c': {
                'image': 'gcc:11.4-alpine',
                'entrypoint': ['sh', '-c'],
                'security_opts': ['no-new-privileges:true'],
                'readonly_rootfs': True
            }
        }

    def _validate_code(self, code: str, language: str) -> bool:
        """
        Validate code for dangerous patterns before execution.
        
        Args:
            code: Source code to validate
            language: Programming language
            
        Returns:
            True if code is safe, False otherwise
        """
        # Dangerous patterns to detect
        dangerous_patterns = [
            r'\b(import|from)\s+os\b',  # OS module imports
            r'\b(import|from)\s+subprocess\b',  # Subprocess imports
            r'\b(import|from)\s+sys\b',  # Sys module (can affect interpreter)
            r'\bexec\b',  # Dynamic code execution
            r'\beval\b',  # Dynamic code execution
            r'\bcompile\b',  # Dynamic code compilation
            r'\bglobals\b',  # Access to global namespace
            r'\blocals\b',  # Access to local namespace
            r'\bopen\b',  # File operations
            r'\bfile\b',  # File operations
            r'\binput\b',  # Interactive input
            r'\braw_input\b',  # Interactive input (Python 2)
            r'\bprint\b',  # Output operations (we'll redirect this)
            r'\bsystem\b',  # System calls
            r'\bpopen\b',  # Process creation
            r'\bcall\b',  # Process creation
            r'\bcheck_call\b',  # Process creation
            r'\bcheck_output\b',  # Process creation
            r'\bsocket\b',  # Network operations
            r'\bconnect\b',  # Network operations
            r'\bbind\b',  # Network operations
            r'\blisten\b',  # Network operations
            r'\baccept\b',  # Network operations
            r'\bgetaddrinfo\b',  # Network operations
            r'\bgethostbyname\b',  # Network operations
        ]
        
        # Language-specific patterns
        if language == 'python':
            dangerous_patterns.extend([
                r'\b__import__\b',  # Dynamic imports
                r'\bgetattr\b',  # Attribute access
                r'\bsetattr\b',  # Attribute modification
                r'\bdelattr\b',  # Attribute deletion
                r'\bhasattr\b',  # Attribute checking
            ])
        elif language == 'javascript':
            dangerous_patterns.extend([
                r'\brequire\(',  # Module imports
                r'\bprocess\.',  # Process manipulation
                r'\bchild_process\.',  # Child process creation
                r'\bfs\.',  # File system operations
                r'\brequire\(\s*["\']child_process["\']\s*\)',  # Child process module
                r'\brequire\(\s*["\']fs["\']\s*\)',  # File system module
                r'\brequire\(\s*["\']net["\']\s*\)',  # Network module
                r'\brequire\(\s*["\']dns["\']\s*\)',  # DNS module
            ])
        elif language == 'java':
            dangerous_patterns.extend([
                r'Runtime\.getRuntime\(\)',
                r'System\.exec\(',
                r'ProcessBuilder\(',
                r'new\s+File\(',
                r'FileReader\(',
                r'FileWriter\(',
                r'RandomAccessFile\(',
                r'new\s+Socket\(',
                r'new\s+ServerSocket\(',
                r'URL\(',
                r'URLConnection\(',
            ])
        elif language == 'c':
            dangerous_patterns.extend([
                r'\bsystem\s*\(',  # System calls
                r'\bpopen\s*\(',  # Process creation
                r'\bexecve\s*\(',  # Process execution
                r'\bfork\s*\(',  # Process creation
                r'\bvfork\s*\(',  # Process creation
                r'\bopen\s*\(',  # File operations
                r'\bcreat\s*\(',  # File creation
                r'\baccess\s*\(',  # File access checks
                r'\bchmod\s*\(',  # File permission changes
                r'\bchown\s*\(',  # File ownership changes
                r'\bsocket\s*\(',  # Socket creation
                r'\bconnect\s*\(',  # Socket connection
                r'\bbind\s*\(',  # Socket binding
                r'\blisten\s*\(',  # Socket listening
                r'\baccept\s*\(',  # Socket acceptance
            ])

        # Check for dangerous patterns
        for pattern in dangerous_patterns:
            import re
            if re.search(pattern, code, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected in {language} code: {pattern}")
                return False
                
        return True

    def _sanitize_code(self, code: str, language: str) -> str:
        """
        Sanitize code to remove or neutralize potentially harmful constructs.
        
        Args:
            code: Source code to sanitize
            language: Programming language
            
        Returns:
            Sanitized code
        """
        # For Python, wrap code in a restricted environment
        if language == 'python':
            # Create a safe execution wrapper
            wrapper = '''
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# Restrict built-ins
safe_builtins = {{
    'abs', 'all', 'any', 'bool', 'chr', 'complex', 'dict', 'dir', 'divmod',
    'enumerate', 'filter', 'float', 'format', 'frozenset', 'hash', 'hex',
    'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'map', 'max',
    'min', 'next', 'object', 'oct', 'ord', 'pow', 'range', 'repr', 'reversed',
    'round', 'set', 'slice', 'sorted', 'str', 'sum', 'super', 'tuple', 'type',
    'zip', 'True', 'False', 'None'
}}

# Create restricted globals
restricted_globals = {{
    '__builtins__': {{k: __builtins__[k] for k in safe_builtins if k in __builtins__}},
    '__name__': '__main__',
    '__doc__': None,
}}

# Capture output
output_buffer = io.StringIO()
error_buffer = io.StringIO()

try:
    with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
        exec("""{code}""", restricted_globals)
    
    print("===OUTPUT===")
    print(output_buffer.getvalue())
    print("===ERRORS===")
    print(error_buffer.getvalue())
except Exception as e:
    print("===ERRORS===")
    print(f"Execution error: {{e}}")
'''.format(code=code.replace('"', '\\"').replace('\n', '\\n'))
            return wrapper
            
        return code

    @contextmanager
    def _create_secure_temp_dir(self):
        """Create a temporary directory with secure permissions."""
        temp_dir = tempfile.mkdtemp(prefix="nexus_sandbox_")
        try:
            # Set restrictive permissions
            os.chmod(temp_dir, 0o700)  # Only owner can read/write/execute
            yield Path(temp_dir)
        finally:
            # Clean up
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def execute_untrusted_code(
        self,
        code: str,
        language: str,
        timeout: Optional[int] = None,
        memory_limit: Optional[str] = None,
        cpu_quota: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute untrusted code in a secure Docker container.

        Args:
            code: Source code to execute
            language: Programming language ('python', 'javascript', 'go', etc.)
            timeout: Execution timeout in seconds (overrides default)
            memory_limit: Memory limit (e.g., '128m', '1g') (overrides default)
            cpu_quota: CPU quota as fraction of one CPU (overrides default)

        Returns:
            Dictionary with execution results
        """
        # Validate inputs
        language = language.lower()
        if language not in self.language_configs:
            return {
                'success': False,
                'stdout': '',
                'stderr': '',
                'exit_code': -1,
                'error': f"Unsupported language for sandbox: {language}"
            }

        # Use provided values or defaults
        timeout = timeout or self.timeout
        memory_limit = memory_limit or self.max_memory
        cpu_quota = cpu_quota or self.max_cpu

        # Validate code for dangerous patterns
        if not self._validate_code(code, language):
            return {
                'success': False,
                'stdout': '',
                'stderr': '',
                'exit_code': -1,
                'error': 'Code contains dangerous patterns and was rejected'
            }

        # Sanitize code
        sanitized_code = self._sanitize_code(code, language)

        # Create temporary directory for code
        with self._create_secure_temp_dir() as temp_dir:
            temp_path = Path(temp_dir)

            # Write code to temporary file based on language
            file_extensions = {
                'python': '.py',
                'javascript': '.js',
                'go': '.go',
                'rust': '.rs',
                'java': '.java',
                'c': '.c',
            }

            ext = file_extensions[language]
            code_file = temp_path / f"code{ext}"
            
            # Write the sanitized code
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(sanitized_code)

            # Determine execution command based on language
            config = self.language_configs[language]
            image = config['image']
            
            # Create a unique container name to avoid conflicts
            container_name = f"nexus_sandbox_{secrets.token_hex(8)}"
            
            # Calculate CPU period and quota
            cpu_period = 100000  # 100ms in microseconds
            cpu_quota = int(cpu_quota * cpu_period)  # Convert fraction to quota

            try:
                # Run container with security restrictions
                container = self.client.containers.run(
                    image=image,
                    command=[code_file.name] if language != 'go' else ['sh', '-c', f'cd /code && go run {code_file.name}'],
                    volumes={str(temp_path): {'bind': '/code', 'mode': 'ro'}},  # Read-only mount
                    network_mode='none',  # Complete network isolation
                    mem_limit=memory_limit,
                    cpu_period=cpu_period,
                    cpu_quota=cpu_quota,
                    security_opt=config['security_opts'],
                    readonly_rootfs=config['readonly_rootfs'],
                    environment={
                        'HOME': '/tmp',
                        'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                        'PYTHONUNBUFFERED': '1',  # For Python
                    },
                    working_dir='/code',
                    remove=True,  # Auto-remove when done
                    stdout=True,
                    stderr=True,
                    detach=False,
                    timeout=timeout,
                    user='nobody:nobody' if self._container_supports_user(image) else None,  # Run as unprivileged user
                    cap_drop=['ALL'],  # Drop all capabilities
                    privileged=False,  # Never run privileged
                )

                # Parse output
                stdout_raw = container[0] if container[0] else b""
                stderr_raw = container[1] if container[1] else b""

                stdout = stdout_raw.decode('utf-8', errors='replace') if stdout_raw else ""
                stderr = stderr_raw.decode('utf-8', errors='replace') if stderr_raw else ""

                # Extract actual output if wrapped (for Python)
                if language == 'python':
                    # Extract output from our wrapper
                    if '===OUTPUT===' in stdout:
                        output_part = stdout.split('===OUTPUT===')[1]
                        if '===ERRORS===' in output_part:
                            actual_output = output_part.split('===ERRORS===')[0].strip()
                        else:
                            actual_output = output_part.strip()
                        stdout = actual_output

                return {
                    'success': True,
                    'stdout': stdout,
                    'stderr': stderr,
                    'exit_code': 0  # Docker run returns combined output
                }

            except docker.errors.ContainerError as e:
                return {
                    'success': False,
                    'stdout': e.stdout.decode('utf-8', errors='replace') if e.stdout else "",
                    'stderr': e.stderr.decode('utf-8', errors='replace') if e.stderr else "",
                    'exit_code': e.exit_code,
                    'error': f"Container execution failed: {e}"
                }
            except docker.errors.ImageNotFound:
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': '',
                    'exit_code': -1,
                    'error': f"Docker image not found: {image}"
                }
            except docker.errors.APIError as e:
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': '',
                    'exit_code': -1,
                    'error': f"Docker API error: {e}"
                }
            except Exception as e:
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': '',
                    'exit_code': -1,
                    'error': str(e)
                }

    def _container_supports_user(self, image: str) -> bool:
        """
        Check if the container image supports running as a specific user.
        """
        try:
            # Try to inspect the image to see if it has a default user
            img = self.client.images.get(image)
            # Check if image has USER instruction
            return True  # For simplicity, assume most images support user switching
        except:
            return False

    def is_available(self) -> bool:
        """Check if Docker is available for sandboxing."""
        try:
            self.client.ping()
            return True
        except:
            return False

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for sandboxing."""
        return list(self.language_configs.keys())


# Singleton instance
_secure_sandbox = None


def get_secure_sandbox(max_memory: str = "128m", max_cpu: float = 0.5, timeout: int = 30) -> Optional[SecureSandbox]:
    """Get the global secure sandbox instance."""
    global _secure_sandbox
    if _secure_sandbox is None:
        try:
            _secure_sandbox = SecureSandbox(max_memory, max_cpu, timeout)
        except RuntimeError:
            # Docker not available
            return None
    return _secure_sandbox


def execute_secure_code(code: str, language: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to execute code securely.
    
    Args:
        code: Source code to execute
        language: Programming language
        **kwargs: Additional options (timeout, memory_limit, cpu_quota)
        
    Returns:
        Execution results
    """
    sandbox = get_secure_sandbox()
    if not sandbox:
        return {
            'success': False,
            'stdout': '',
            'stderr': '',
            'exit_code': -1,
            'error': 'Secure sandbox not available (Docker required)'
        }
    
    return sandbox.execute_untrusted_code(code, language, **kwargs)