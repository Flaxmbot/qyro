"""
Nexus Platform Abstraction Layer
Provides cross-platform utilities for path handling, executable extensions,
and command execution. Abstracts away Windows vs Unix differences.
"""

import os
import sys
import subprocess
import shutil
import platform
from typing import List, Optional, Tuple, Union
from pathlib import Path
from enum import Enum

from .logging import get_logger

logger = get_logger("nexus.platform")


class PlatformType(Enum):
    """Supported platform types."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class Platform:
    """
    Platform abstraction layer for cross-platform compatibility.
    
    Provides utilities for:
    - Path handling (Windows vs Unix paths)
    - Executable extensions (.exe on Windows, none on Unix)
    - Command execution and subprocess handling
    - Platform-specific operations
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure consistent platform detection."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize platform detection."""
        if self._initialized:
            return
        
        self._initialized = True
        self._detect_platform()
        self._setup_platform_specifics()
    
    def _detect_platform(self):
        """Detect the current platform."""
        if sys.platform == 'win32':
            self.type = PlatformType.WINDOWS
            self.name = 'windows'
        elif sys.platform == 'darwin':
            self.type = PlatformType.MACOS
            self.name = 'macos'
        elif sys.platform.startswith('linux'):
            self.type = PlatformType.LINUX
            self.name = 'linux'
        else:
            self.type = PlatformType.UNKNOWN
            self.name = 'unknown'
        
        logger.info("platform_detected", platform=self.name, sys_platform=sys.platform)
    
    def _setup_platform_specifics(self):
        """Setup platform-specific settings."""
        # Path separator
        self.path_sep = os.sep
        self.path_list_sep = os.pathsep
        
        # Executable extension
        self.exe_extension = '.exe' if self.type == PlatformType.WINDOWS else ''
        
        # Shell settings
        self.use_shell = self.type == PlatformType.WINDOWS
        
        # Default shell
        if self.type == PlatformType.WINDOWS:
            self.default_shell = os.environ.get('COMSPEC', 'cmd.exe')
        else:
            self.default_shell = os.environ.get('SHELL', '/bin/sh')
        
        # Newline
        self.newline = os.linesep
        
        # Null device
        self.null_device = 'NUL' if self.type == PlatformType.WINDOWS else '/dev/null'
        
        # Temporary directory
        self.temp_dir = os.environ.get('TEMP', '/tmp') if self.type == PlatformType.WINDOWS else '/tmp'
        
        # Home directory
        self.home_dir = os.path.expanduser('~')
    
    # Path handling methods
    
    def normalize_path(self, path: str) -> str:
        """
        Normalize a path for the current platform.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        # Convert to absolute path
        path = os.path.abspath(path)
        
        # Normalize path separators
        path = os.path.normpath(path)
        
        return path
    
    def join_path(self, *parts: str) -> str:
        """
        Join path parts using the platform-specific separator.
        
        Args:
            *parts: Path parts to join
            
        Returns:
            Joined path
        """
        return os.path.join(*parts)
    
    def split_path(self, path: str) -> List[str]:
        """
        Split a path into components.
        
        Args:
            path: Path to split
            
        Returns:
            List of path components
        """
        return list(Path(path).parts)
    
    def get_basename(self, path: str) -> str:
        """
        Get the basename (filename) from a path.
        
        Args:
            path: Path to extract basename from
            
        Returns:
            Basename
        """
        return os.path.basename(path)
    
    def get_dirname(self, path: str) -> str:
        """
        Get the directory name from a path.
        
        Args:
            path: Path to extract directory from
            
        Returns:
            Directory name
        """
        return os.path.dirname(path)
    
    def get_extension(self, path: str) -> str:
        """
        Get the file extension from a path.
        
        Args:
            path: Path to extract extension from
            
        Returns:
            File extension (including the dot)
        """
        return os.path.splitext(path)[1]
    
    def remove_extension(self, path: str) -> str:
        """
        Remove the file extension from a path.
        
        Args:
            path: Path to remove extension from
            
        Returns:
            Path without extension
        """
        return os.path.splitext(path)[0]
    
    # Executable handling methods
    
    def get_executable_name(self, name: str) -> str:
        """
        Add platform-specific executable extension to a name.
        
        Args:
            name: Base name of the executable
            
        Returns:
            Name with appropriate extension
        """
        if not name.endswith(self.exe_extension):
            return name + self.exe_extension
        return name
    
    def is_executable(self, path: str) -> bool:
        """
        Check if a file is executable.
        
        Args:
            path: Path to check
            
        Returns:
            True if executable, False otherwise
        """
        if not os.path.isfile(path):
            return False
        
        if self.type == PlatformType.WINDOWS:
            # On Windows, check for executable extensions
            ext = self.get_extension(path).lower()
            return ext in ['.exe', '.bat', '.cmd', '.ps1']
        else:
            # On Unix, check execute permission
            return os.access(path, os.X_OK)
    
    def which(self, command: str) -> Optional[str]:
        """
        Find the full path to an executable command.
        
        Args:
            command: Command to find
            
        Returns:
            Full path if found, None otherwise
        """
        return shutil.which(command)
    
    # Command execution methods
    
    def run_command(
        self,
        cmd: Union[str, List[str]],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[int] = None,
        capture_output: bool = True,
        shell: Optional[bool] = None,
        text: bool = True,
    ) -> Tuple[int, str, str]:
        """
        Run a command with cross-platform compatibility.
        
        Args:
            cmd: Command to run (string or list)
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
            shell: Whether to use shell (default: platform-specific)
            text: Whether to return text instead of bytes
            
        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        if shell is None:
            shell = self.use_shell
        
        # Convert string command to list if needed
        if isinstance(cmd, str) and not shell:
            # On Unix, we need to split the command
            if self.type != PlatformType.WINDOWS:
                import shlex
                cmd = shlex.split(cmd)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                timeout=timeout,
                capture_output=capture_output,
                shell=shell,
                text=text,
                encoding='utf-8',
                errors='replace'
            )
            return result.returncode, result.stdout, result.stderr
        except FileNotFoundError:
            return 1, "", f"Command not found: {cmd}"
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return 1, "", str(e)
    
    def kill_process(self, pid: int, force: bool = False) -> bool:
        """
        Kill a process by PID.
        
        Args:
            pid: Process ID
            force: Whether to force kill
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.type == PlatformType.WINDOWS:
                import signal
                sig = signal.SIGTERM if not force else signal.SIGKILL
                os.kill(pid, sig)
            else:
                import signal
                sig = signal.SIGTERM if not force else signal.SIGKILL
                os.kill(pid, sig)
            return True
        except Exception as e:
            logger.warning("kill_process_failed", pid=pid, error=str(e))
            return False
    
    def kill_process_by_name(self, name: str, force: bool = False) -> bool:
        """
        Kill processes by name.

        Args:
            name: Process name (exact match, no wildcards)
            force: Whether to force kill

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.type == PlatformType.WINDOWS:
                # Use wmic to get exact process names and then kill by PID
                # This prevents killing processes that start with the same name
                cmd = ['wmic', 'process', 'where', f'name="{name}"', 'get', 'processid', '/value']
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0 and result.stdout.strip():
                    # Extract PIDs from wmic output
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip().startswith('ProcessId='):
                            try:
                                pid = int(line.split('=')[1].strip())
                                if pid > 0:
                                    self.kill_process(pid, force)
                            except (ValueError, IndexError):
                                continue
                    return True
                else:
                    # Fallback to tasklist to find exact matches
                    cmd = ['tasklist', '/FI', f'IMAGENAME eq {name}', '/FO', 'CSV']
                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode == 0 and result.stdout.strip():
                        lines = result.stdout.strip().split('\n')
                        for line in lines[1:]:  # Skip header
                            if line:
                                try:
                                    # CSV format: "process_name.exe",PID,...
                                    process_name = line.split(',')[0].strip().strip('"')
                                    if process_name.lower() == name.lower():
                                        pid = int(line.split(',')[1].strip().strip('"'))
                                        self.kill_process(pid, force)
                                except (ValueError, IndexError):
                                    continue
                    return True
            else:
                # Use pgrep to get exact process IDs on Unix systems
                cmd = ['pgrep', '-f', f'^{name}$|^./{name}$']
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid_str in pids:
                        try:
                            pid = int(pid_str.strip())
                            self.kill_process(pid, force)
                        except ValueError:
                            continue
                else:
                    # Fallback: use pkill with exact match
                    cmd = ['pkill', '-x', name]  # -x for exact match
                    if force:
                        cmd.insert(1, '-9')
                    result = subprocess.run(cmd, capture_output=True)
                    return result.returncode == 0
                return True
        except Exception as e:
            logger.warning("kill_process_by_name_failed", name=name, error=str(e))
            return False
    
    # File system methods
    
    def ensure_dir(self, path: str) -> str:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Directory path
            
        Returns:
            Path to the directory
        """
        os.makedirs(path, exist_ok=True)
        return path
    
    def remove_file(self, path: str) -> bool:
        """
        Remove a file if it exists.
        
        Args:
            path: Path to file
            
        Returns:
            True if removed or didn't exist, False on error
        """
        try:
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception as e:
            logger.warning("remove_file_failed", path=path, error=str(e))
            return False
    
    def remove_dir(self, path: str) -> bool:
        """
        Remove a directory if it exists.
        
        Args:
            path: Path to directory
            
        Returns:
            True if removed or didn't exist, False on error
        """
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
            return True
        except Exception as e:
            logger.warning("remove_dir_failed", path=path, error=str(e))
            return False
    
    # Environment methods
    
    def get_env_var(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an environment variable.
        
        Args:
            name: Variable name
            default: Default value if not found
            
        Returns:
            Variable value or default
        """
        return os.environ.get(name, default)
    
    def set_env_var(self, name: str, value: str):
        """
        Set an environment variable.
        
        Args:
            name: Variable name
            value: Variable value
        """
        os.environ[name] = value
    
    def get_path_env(self) -> List[str]:
        """
        Get the PATH environment variable as a list.
        
        Returns:
            List of paths
        """
        path_str = self.get_env_var('PATH', '')
        return path_str.split(self.path_list_sep) if path_str else []
    
    def add_to_path(self, path: str, prepend: bool = True):
        """
        Add a path to the PATH environment variable.
        
        Args:
            path: Path to add
            prepend: Whether to add to the beginning
        """
        current_path = self.get_path_env()
        
        if path in current_path:
            return  # Already in PATH
        
        if prepend:
            current_path.insert(0, path)
        else:
            current_path.append(path)
        
        self.set_env_var('PATH', self.path_list_sep.join(current_path))
    
    # Utility methods
    
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self.type == PlatformType.WINDOWS
    
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self.type == PlatformType.LINUX
    
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self.type == PlatformType.MACOS
    
    def get_platform_info(self) -> dict:
        """
        Get platform information.
        
        Returns:
            Dictionary with platform details
        """
        return {
            'type': self.type.value,
            'name': self.name,
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'executable_extension': self.exe_extension,
            'path_separator': self.path_sep,
        }
    
    def print_platform_info(self):
        """Print platform information."""
        info = self.get_platform_info()
        print("\n" + "=" * 60)
        print("PLATFORM INFORMATION")
        print("=" * 60)
        for key, value in info.items():
            print(f"{key:20}: {value}")
        print("=" * 60 + "\n")


# Global platform instance
_platform = None


def get_platform() -> Platform:
    """
    Get the global platform instance.
    
    Returns:
        Platform instance
    """
    global _platform
    if _platform is None:
        _platform = Platform()
    return _platform


# Convenience functions for common operations

def normalize_path(path: str) -> str:
    """Normalize a path for the current platform."""
    return get_platform().normalize_path(path)


def join_path(*parts: str) -> str:
    """Join path parts using the platform-specific separator."""
    return get_platform().join_path(*parts)


def get_executable_name(name: str) -> str:
    """Add platform-specific executable extension to a name."""
    return get_platform().get_executable_name(name)


def run_command(cmd: Union[str, List[str]], **kwargs) -> Tuple[int, str, str]:
    """Run a command with cross-platform compatibility."""
    return get_platform().run_command(cmd, **kwargs)


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform().is_windows()


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_platform().is_linux()


def is_macos() -> bool:
    """Check if running on macOS."""
    return get_platform().is_macos()


if __name__ == "__main__":
    # Print platform information when executed directly
    platform = get_platform()
    platform.print_platform_info()
