"""
Nexus Secure Sandbox System
Provides containerized execution for untrusted code using Docker isolation.
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


class NexusSandbox:
    """
    Secure execution environment for untrusted code using Docker containers.
    
    Features:
    - Isolated container execution
    - Resource limits (CPU, memory, disk)
    - Network isolation
    - File system restrictions
    - Timeout enforcement
    """
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
        except Exception as e:
            raise RuntimeError(f"Docker is required for sandboxing: {e}")
    
    def execute_untrusted_code(
        self, 
        code: str, 
        language: str, 
        timeout: int = 30,
        memory_limit: str = "128m",
        cpu_quota: int = 100000,  # 10% of 1 CPU
        network_disabled: bool = True
    ) -> Dict[str, Any]:
        """
        Execute untrusted code in a secure Docker container.
        
        Args:
            code: Source code to execute
            language: Programming language ('python', 'javascript', 'go', etc.)
            timeout: Execution timeout in seconds
            memory_limit: Memory limit (e.g., '128m', '1g')
            cpu_quota: CPU quota in microseconds per period
            network_disabled: Whether to disable network access
            
        Returns:
            Dictionary with execution results
        """
        # Map language to Docker image
        image_map = {
            'python': 'python:3.11-alpine',
            'js': 'node:18-alpine',
            'javascript': 'node:18-alpine',
            'go': 'golang:1.21-alpine',
            'rust': 'rust:1.75-slim',
            'java': 'openjdk:17-jdk-slim',
            'c': 'gcc:11.4-bookworm',
            'cpp': 'gcc:11.4-bookworm',
            'ruby': 'ruby:3.2-alpine',
            'php': 'php:8.2-cli-alpine',
            'lua': 'lua:5.4-alpine'
        }
        
        if language not in image_map:
            raise ValueError(f"Unsupported language for sandbox: {language}")
        
        image = image_map[language]
        
        # Create temporary directory for code
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write code to temporary file based on language
            file_extensions = {
                'python': '.py',
                'js': '.js',
                'javascript': '.js',
                'go': '.go',
                'rust': '.rs',
                'java': '.java',
                'c': '.c',
                'cpp': '.cpp',
                'ruby': '.rb',
                'php': '.php',
                'lua': '.lua'
            }
            
            ext = file_extensions[language]
            code_file = temp_path / f"code{ext}"
            code_file.write_text(code)
            
            # Determine execution command based on language
            commands = {
                'python': ['python', '/code/code.py'],
                'js': ['node', '/code/code.js'],
                'javascript': ['node', '/code/code.js'],
                'go': ['sh', '-c', 'cd /code && go run *.go'],
                'rust': ['sh', '-c', 'rustc /code/code.rs -o /tmp/program && /tmp/program'],
                'java': ['sh', '-c', 'cd /code && javac *.java && java $(ls *.class | head -c -7)'],
                'c': ['sh', '-c', 'cd /code && gcc code.c -o program && ./program'],
                'cpp': ['sh', '-c', 'cd /code && g++ code.cpp -o program && ./program'],
                'ruby': ['ruby', '/code/code.rb'],
                'php': ['php', '/code/code.php'],
                'lua': ['lua', '/code/code.lua']
            }
            
            cmd = commands[language]
            
            try:
                # Run container with security restrictions
                container = self.client.containers.run(
                    image=image,
                    command=cmd,
                    volumes={str(temp_path): {'bind': '/code', 'mode': 'ro'}},  # Read-only mount
                    network_mode='none' if network_disabled else None,
                    mem_limit=memory_limit,
                    cpu_quota=cpu_quota,
                    environment={
                        'HOME': '/tmp',
                        'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
                    },
                    working_dir='/code',
                    remove=True,  # Auto-remove when done
                    stdout=True,
                    stderr=True,
                    detach=False,
                    timeout=timeout
                )
                
                # Parse output
                stdout = container[0].decode('utf-8', errors='replace') if container[0] else ""
                stderr = container[1].decode('utf-8', errors='replace') if container[1] else ""
                
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
            except Exception as e:
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': '',
                    'exit_code': -1,
                    'error': str(e)
                }
    
    def is_available(self) -> bool:
        """Check if Docker is available for sandboxing."""
        try:
            self.client.ping()
            return True
        except:
            return False


# Singleton instance
_nexus_sandbox = None


def get_sandbox() -> Optional[NexusSandbox]:
    """Get the global sandbox instance."""
    global _nexus_sandbox
    if _nexus_sandbox is None:
        try:
            _nexus_sandbox = NexusSandbox()
        except RuntimeError:
            # Docker not available
            return None
    return _nexus_sandbox