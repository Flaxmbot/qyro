"""
Nexus Toolchain Validator
Provides pre-flight validation for all supported language toolchains.
Checks availability and minimum versions with platform-specific installation instructions.
"""

import subprocess
import sys
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .logging import get_logger

logger = get_logger("nexus.toolchain_validator")


class ToolchainStatus(Enum):
    """Status of a toolchain check."""
    AVAILABLE = "available"
    MISSING = "missing"
    VERSION_TOO_OLD = "version_too_old"
    ERROR = "error"


@dataclass
class ToolchainCheck:
    """Result of a toolchain check."""
    name: str
    status: ToolchainStatus
    version: Optional[str] = None
    error_message: Optional[str] = None
    install_instructions: Optional[str] = None


class ToolchainValidator:
    """
    Validates toolchain availability and versions for all supported languages.
    
    Supported Languages:
    - C (gcc/clang)
    - Java (javac)
    - Rust (cargo)
    - Go (go)
    - Node.js (node/npm)
    - Python (python)
    """
    
    # Minimum version requirements
    MIN_VERSIONS = {
        'gcc': '9.0',
        'clang': '11.0',
        'javac': '11',
        'cargo': '1.70',
        'go': '1.20',
        'node': '18.0.0',
        'python': '3.8',
    }
    
    # Recommended versions
    RECOMMENDED_VERSIONS = {
        'gcc': '11.0',
        'clang': '15.0',
        'javac': '17',
        'cargo': '1.75',
        'go': '1.21',
        'node': '20.0.0',
        'python': '3.11',
    }
    
    # Platform-specific installation commands
    INSTALL_COMMANDS = {
        'linux': {
            'gcc': 'sudo apt install gcc || sudo yum install gcc',
            'clang': 'sudo apt install clang || sudo yum install clang',
            'javac': 'sudo apt install openjdk-17-jdk || sudo yum install java-17-openjdk-devel',
            'cargo': 'curl --proto \'=https\' --tlsv1.2 -sSf https://sh.rustup.rs | sh',
            'go': 'wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz && sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz',
            'node': 'curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install nodejs',
            'python': 'sudo apt install python3 python3-pip || sudo yum install python3 python3-pip',
        },
        'darwin': {  # macOS
            'gcc': 'xcode-select --install',
            'clang': 'xcode-select --install',
            'javac': 'brew install openjdk@17',
            'cargo': 'curl --proto \'=https\' --tlsv1.2 -sSf https://sh.rustup.rs | sh',
            'go': 'brew install go',
            'node': 'brew install node',
            'python': 'brew install python',
        },
        'win32': {  # Windows
            'gcc': 'Download and install MinGW-w64 from https://www.mingw-w64.org/ or use: choco install mingw',
            'clang': 'Download and install LLVM from https://llvm.org/ or use: choco install llvm',
            'javac': 'Download and install JDK 17 from https://adoptium.net/ or use: choco install temurin17jdk',
            'cargo': 'Download and install from https://rustup.rs/ or use: choco install rust',
            'go': 'Download and install from https://go.dev/dl/ or use: choco install golang',
            'node': 'Download and install from https://nodejs.org/ or use: choco install nodejs',
            'python': 'Download and install from https://python.org/ or use: choco install python',
        },
    }
    
    def __init__(self):
        self.platform = self._detect_platform()
        self.checks: Dict[str, ToolchainCheck] = {}
    
    def _detect_platform(self) -> str:
        """Detect the current platform."""
        if sys.platform == 'win32':
            return 'win32'
        elif sys.platform == 'darwin':
            return 'darwin'
        else:
            return 'linux'
    
    def _get_install_command(self, tool: str) -> str:
        """Get platform-specific installation command for a tool."""
        return self.INSTALL_COMMANDS.get(self.platform, {}).get(
            tool, 
            f"Please install {tool} manually"
        )
    
    def _run_command(self, cmd: List[str], timeout: int = 5) -> Tuple[int, str, str]:
        """
        Run a command and return (returncode, stdout, stderr).
        
        Args:
            cmd: Command to run as a list
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return result.returncode, result.stdout, result.stderr
        except FileNotFoundError:
            return 1, "", "Command not found"
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def _parse_version(self, version_string: str, tool: str) -> Optional[str]:
        """
        Parse version string from tool output.
        
        Args:
            version_string: Raw version output from tool
            tool: Name of the tool
            
        Returns:
            Parsed version string or None
        """
        version_string = version_string.strip()
        
        # Tool-specific version parsing patterns
        patterns = {
            'gcc': r'gcc\s+\(.*?\)\s+([\d.]+)',
            'clang': r'clang\s+version\s+([\d.]+)',
            'javac': r'javac\s+([\d.]+)',
            'cargo': r'cargo\s+([\d.]+)',
            'go': r'go\s+version\s+go([\d.]+)',
            'node': r'v?([\d.]+)',
            'python': r'Python\s+([\d.]+)',
        }
        
        pattern = patterns.get(tool)
        if pattern:
            match = re.search(pattern, version_string)
            if match:
                return match.group(1)
        
        # Fallback: try to extract first version-like string
        version_match = re.search(r'(\d+(?:\.\d+)*)', version_string)
        if version_match:
            return version_match.group(1)
        
        return None
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
        
        return 0
    
    def check_gcc(self) -> ToolchainCheck:
        """Check for GCC compiler."""
        returncode, stdout, stderr = self._run_command(['gcc', '--version'])
        
        if returncode != 0:
            return ToolchainCheck(
                name='gcc',
                status=ToolchainStatus.MISSING,
                install_instructions=self._get_install_command('gcc')
            )
        
        version = self._parse_version(stdout, 'gcc')
        if not version:
            return ToolchainCheck(
                name='gcc',
                status=ToolchainStatus.ERROR,
                error_message='Could not parse version',
                install_instructions=self._get_install_command('gcc')
            )
        
        min_version = self.MIN_VERSIONS.get('gcc', '9.0')
        if self._compare_versions(version, min_version) < 0:
            return ToolchainCheck(
                name='gcc',
                status=ToolchainStatus.VERSION_TOO_OLD,
                version=version,
                error_message=f'GCC version {version} is too old (minimum: {min_version})',
                install_instructions=self._get_install_command('gcc')
            )
        
        return ToolchainCheck(
            name='gcc',
            status=ToolchainStatus.AVAILABLE,
            version=version
        )
    
    def check_clang(self) -> ToolchainCheck:
        """Check for Clang compiler."""
        returncode, stdout, stderr = self._run_command(['clang', '--version'])
        
        if returncode != 0:
            return ToolchainCheck(
                name='clang',
                status=ToolchainStatus.MISSING,
                install_instructions=self._get_install_command('clang')
            )
        
        version = self._parse_version(stdout, 'clang')
        if not version:
            return ToolchainCheck(
                name='clang',
                status=ToolchainStatus.ERROR,
                error_message='Could not parse version',
                install_instructions=self._get_install_command('clang')
            )
        
        min_version = self.MIN_VERSIONS.get('clang', '11.0')
        if self._compare_versions(version, min_version) < 0:
            return ToolchainCheck(
                name='clang',
                status=ToolchainStatus.VERSION_TOO_OLD,
                version=version,
                error_message=f'Clang version {version} is too old (minimum: {min_version})',
                install_instructions=self._get_install_command('clang')
            )
        
        return ToolchainCheck(
            name='clang',
            status=ToolchainStatus.AVAILABLE,
            version=version
        )
    
    def check_javac(self) -> ToolchainCheck:
        """Check for Java compiler."""
        returncode, stdout, stderr = self._run_command(['javac', '-version'])
        
        if returncode != 0:
            return ToolchainCheck(
                name='javac',
                status=ToolchainStatus.MISSING,
                install_instructions=self._get_install_command('javac')
            )
        
        # javac -version may output to stdout or stderr depending on platform
        version_output = stdout if stdout else stderr
        version = self._parse_version(version_output, 'javac')
        if not version:
            return ToolchainCheck(
                name='javac',
                status=ToolchainStatus.ERROR,
                error_message='Could not parse version',
                install_instructions=self._get_install_command('javac')
            )
        
        min_version = self.MIN_VERSIONS.get('javac', '11')
        if self._compare_versions(version, min_version) < 0:
            return ToolchainCheck(
                name='javac',
                status=ToolchainStatus.VERSION_TOO_OLD,
                version=version,
                error_message=f'Java version {version} is too old (minimum: {min_version})',
                install_instructions=self._get_install_command('javac')
            )
        
        return ToolchainCheck(
            name='javac',
            status=ToolchainStatus.AVAILABLE,
            version=version
        )
    
    def check_cargo(self) -> ToolchainCheck:
        """Check for Cargo (Rust)."""
        returncode, stdout, stderr = self._run_command(['cargo', '--version'])
        
        if returncode != 0:
            return ToolchainCheck(
                name='cargo',
                status=ToolchainStatus.MISSING,
                install_instructions=self._get_install_command('cargo')
            )
        
        version = self._parse_version(stdout, 'cargo')
        if not version:
            return ToolchainCheck(
                name='cargo',
                status=ToolchainStatus.ERROR,
                error_message='Could not parse version',
                install_instructions=self._get_install_command('cargo')
            )
        
        min_version = self.MIN_VERSIONS.get('cargo', '1.70')
        if self._compare_versions(version, min_version) < 0:
            return ToolchainCheck(
                name='cargo',
                status=ToolchainStatus.VERSION_TOO_OLD,
                version=version,
                error_message=f'Cargo version {version} is too old (minimum: {min_version})',
                install_instructions=self._get_install_command('cargo')
            )
        
        return ToolchainCheck(
            name='cargo',
            status=ToolchainStatus.AVAILABLE,
            version=version
        )
    
    def check_go(self) -> ToolchainCheck:
        """Check for Go compiler."""
        returncode, stdout, stderr = self._run_command(['go', 'version'])
        
        if returncode != 0:
            return ToolchainCheck(
                name='go',
                status=ToolchainStatus.MISSING,
                install_instructions=self._get_install_command('go')
            )
        
        version = self._parse_version(stdout, 'go')
        if not version:
            return ToolchainCheck(
                name='go',
                status=ToolchainStatus.ERROR,
                error_message='Could not parse version',
                install_instructions=self._get_install_command('go')
            )
        
        min_version = self.MIN_VERSIONS.get('go', '1.20')
        if self._compare_versions(version, min_version) < 0:
            return ToolchainCheck(
                name='go',
                status=ToolchainStatus.VERSION_TOO_OLD,
                version=version,
                error_message=f'Go version {version} is too old (minimum: {min_version})',
                install_instructions=self._get_install_command('go')
            )
        
        return ToolchainCheck(
            name='go',
            status=ToolchainStatus.AVAILABLE,
            version=version
        )
    
    def check_node(self) -> ToolchainCheck:
        """Check for Node.js."""
        returncode, stdout, stderr = self._run_command(['node', '--version'])
        
        if returncode != 0:
            return ToolchainCheck(
                name='node',
                status=ToolchainStatus.MISSING,
                install_instructions=self._get_install_command('node')
            )
        
        version = self._parse_version(stdout, 'node')
        if not version:
            return ToolchainCheck(
                name='node',
                status=ToolchainStatus.ERROR,
                error_message='Could not parse version',
                install_instructions=self._get_install_command('node')
            )
        
        min_version = self.MIN_VERSIONS.get('node', '18.0.0')
        if self._compare_versions(version, min_version) < 0:
            return ToolchainCheck(
                name='node',
                status=ToolchainStatus.VERSION_TOO_OLD,
                version=version,
                error_message=f'Node.js version {version} is too old (minimum: {min_version})',
                install_instructions=self._get_install_command('node')
            )
        
        return ToolchainCheck(
            name='node',
            status=ToolchainStatus.AVAILABLE,
            version=version
        )
    
    def check_python(self) -> ToolchainCheck:
        """Check for Python."""
        returncode, stdout, stderr = self._run_command([sys.executable, '--version'])
        
        if returncode != 0:
            return ToolchainCheck(
                name='python',
                status=ToolchainStatus.MISSING,
                install_instructions=self._get_install_command('python')
            )
        
        version = self._parse_version(stdout, 'python')
        if not version:
            return ToolchainCheck(
                name='python',
                status=ToolchainStatus.ERROR,
                error_message='Could not parse version',
                install_instructions=self._get_install_command('python')
            )
        
        min_version = self.MIN_VERSIONS.get('python', '3.8')
        if self._compare_versions(version, min_version) < 0:
            return ToolchainCheck(
                name='python',
                status=ToolchainStatus.VERSION_TOO_OLD,
                version=version,
                error_message=f'Python version {version} is too old (minimum: {min_version})',
                install_instructions=self._get_install_command('python')
            )
        
        return ToolchainCheck(
            name='python',
            status=ToolchainStatus.AVAILABLE,
            version=version
        )
    
    def check_all(self) -> Dict[str, ToolchainCheck]:
        """
        Check all toolchains.
        
        Returns:
            Dictionary mapping toolchain names to check results
        """
        self.checks = {
            'gcc': self.check_gcc(),
            'clang': self.check_clang(),
            'javac': self.check_javac(),
            'cargo': self.check_cargo(),
            'go': self.check_go(),
            'node': self.check_node(),
            'python': self.check_python(),
        }
        
        return self.checks
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of languages with available toolchains.
        
        Returns:
            List of language names that have available toolchains
        """
        available = []
        
        # Check C compilers
        if self.checks.get('gcc', ToolchainCheck('gcc', ToolchainStatus.MISSING)).status == ToolchainStatus.AVAILABLE:
            available.append('c')
        if self.checks.get('clang', ToolchainCheck('clang', ToolchainStatus.MISSING)).status == ToolchainStatus.AVAILABLE:
            available.append('c')
        
        # Check other languages
        if self.checks.get('javac', ToolchainCheck('javac', ToolchainStatus.MISSING)).status == ToolchainStatus.AVAILABLE:
            available.append('java')
        if self.checks.get('cargo', ToolchainCheck('cargo', ToolchainStatus.MISSING)).status == ToolchainStatus.AVAILABLE:
            available.append('rust')
        if self.checks.get('go', ToolchainCheck('go', ToolchainStatus.MISSING)).status == ToolchainStatus.AVAILABLE:
            available.append('go')
        if self.checks.get('node', ToolchainCheck('node', ToolchainStatus.MISSING)).status == ToolchainStatus.AVAILABLE:
            available.append('typescript')
        if self.checks.get('python', ToolchainCheck('python', ToolchainStatus.MISSING)).status == ToolchainStatus.AVAILABLE:
            available.append('python')
        
        return list(set(available))  # Remove duplicates
    
    def is_language_available(self, language: str) -> bool:
        """
        Check if a specific language toolchain is available.
        
        Args:
            language: Language name (c, java, rust, go, typescript, python)
            
        Returns:
            True if toolchain is available, False otherwise
        """
        language_map = {
            'c': ['gcc', 'clang'],
            'java': ['javac'],
            'rust': ['cargo'],
            'go': ['go'],
            'typescript': ['node'],
            'ts': ['node'],
            'python': ['python'],
            'py': ['python'],
        }
        
        tools = language_map.get(language.lower(), [])
        for tool in tools:
            check = self.checks.get(tool)
            if check and check.status == ToolchainStatus.AVAILABLE:
                return True
        
        return False
    
    def print_report(self):
        """Print a formatted report of all toolchain checks."""
        print("\n" + "=" * 70)
        print("NEXUS TOOLCHAIN VALIDATION REPORT")
        print("=" * 70)
        print(f"Platform: {self.platform}")
        print("=" * 70)
        
        available_count = 0
        missing_count = 0
        warning_count = 0
        
        for tool, check in self.checks.items():
            status_icon = {
                ToolchainStatus.AVAILABLE: "✓",
                ToolchainStatus.MISSING: "✗",
                ToolchainStatus.VERSION_TOO_OLD: "⚠",
                ToolchainStatus.ERROR: "!",
            }.get(check.status, "?")
            
            status_color = {
                ToolchainStatus.AVAILABLE: "green",
                ToolchainStatus.MISSING: "red",
                ToolchainStatus.VERSION_TOO_OLD: "yellow",
                ToolchainStatus.ERROR: "red",
            }.get(check.status, "white")
            
            version_str = f" (v{check.version})" if check.version else ""
            
            if check.status == ToolchainStatus.AVAILABLE:
                available_count += 1
            elif check.status == ToolchainStatus.MISSING:
                missing_count += 1
            else:
                warning_count += 1
            
            print(f"{status_icon} {tool.upper():10} {check.status.value:20} {version_str}")
            
            if check.error_message:
                print(f"  └─ {check.error_message}")
            
            if check.install_instructions:
                print(f"  └─ Install: {check.install_instructions}")
        
        print("=" * 70)
        print(f"Summary: {available_count} available, {missing_count} missing, {warning_count} warnings")
        print("=" * 70)
        
        if missing_count > 0 or warning_count > 0:
            print("\n⚠ Some toolchains are missing or outdated.")
            print("You can still use Nexus with available languages.")
            print("Install missing toolchains for full functionality.\n")
        else:
            print("\n✓ All toolchains are available and up to date!\n")


def validate_toolchains() -> ToolchainValidator:
    """
    Convenience function to validate all toolchains.
    
    Returns:
        ToolchainValidator instance with check results
    """
    validator = ToolchainValidator()
    validator.check_all()
    return validator


if __name__ == "__main__":
    # Run validation when executed directly
    validator = validate_toolchains()
    validator.print_report()
