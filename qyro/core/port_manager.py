"""
Port Management Utility for Qyro

Provides:
- Port availability checking
- Dynamic port assignment with fallbacks
- Service URL display
"""

import socket
from typing import Dict, Tuple, Optional
from rich.console import Console
from rich.table import Table

console = Console()

# Default port assignments
DEFAULT_PORTS = {
    "frontend": 3000,
    "web": 3000,
    "api": 8000,
    "python": 8000,
    "java": 8080,
    "rust": 8081,
    "go": 8082,
    "c": 8083,
    "cpp": 8083,
    "node": 3000,
    "redis": 6379,
    "kafka": 9092,
}

# Port ranges for fallback
PORT_RANGES = {
    "frontend": (3000, 3100),
    "web": (3000, 3100),
    "api": (8000, 8100),
    "python": (8000, 8100),
    "java": (8080, 8180),
    "rust": (8081, 8181),
    "go": (8082, 8182),
    "c": (8083, 8183),
    "cpp": (8083, 8183),
    "node": (3000, 3100),
}


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is available on the given host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # Port is available if connect fails
    except socket.error:
        return True  # Assume available if we can't check


def find_available_port(service_type: str, preferred_port: Optional[int] = None) -> int:
    """
    Find an available port for the given service type.
    
    Args:
        service_type: Type of service (frontend, api, python, etc.)
        preferred_port: Optional preferred port to try first
        
    Returns:
        An available port number
    """
    # Try preferred port first
    if preferred_port and is_port_available(preferred_port):
        return preferred_port
    
    # Try default port for this service type
    default_port = DEFAULT_PORTS.get(service_type.lower(), 8000)
    if is_port_available(default_port):
        return default_port
    
    # Get port range and search for available port
    port_range = PORT_RANGES.get(service_type.lower(), (8000, 8100))
    for port in range(port_range[0], port_range[1]):
        if is_port_available(port):
            return port
    
    # Last resort: find any available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def assign_ports(services: Dict[str, str]) -> Dict[str, int]:
    """
    Assign ports to all services, checking availability.
    
    Args:
        services: Dict of service_name -> service_type
        
    Returns:
        Dict of service_name -> assigned_port
    """
    assigned = {}
    used_ports = set()
    
    for service_name, service_type in services.items():
        default = DEFAULT_PORTS.get(service_type.lower(), 8000)
        
        # Find available port that's not already assigned
        port = default
        while not is_port_available(port) or port in used_ports:
            port += 1
            if port > default + 100:
                # Fallback to random available port
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', 0))
                    port = s.getsockname()[1]
                break
        
        assigned[service_name] = port
        used_ports.add(port)
    
    return assigned


def display_service_urls(port_assignments: Dict[str, int], service_types: Dict[str, str]):
    """Display service URLs in a nice table."""
    table = Table(title="🚀 Service URLs", show_header=True, header_style="bold cyan")
    table.add_column("Service", style="bold")
    table.add_column("Type", style="dim")
    table.add_column("URL", style="green")
    table.add_column("Status", style="bold")
    
    for service_name, port in port_assignments.items():
        service_type = service_types.get(service_name, "unknown")
        
        # Determine URL based on service type
        if service_type.lower() in ("web", "frontend", "node"):
            url = f"http://localhost:{port}"
        elif service_type.lower() in ("python", "api", "java", "rust", "go"):
            url = f"http://localhost:{port}"
        else:
            url = f"localhost:{port}"
        
        table.add_row(service_name, service_type, url, "✅ Ready")
    
    console.print()
    console.print(table)
    console.print()


def generate_docker_compose_ports(services: Dict[str, str]) -> Tuple[Dict[str, int], str]:
    """
    Generate port mappings for docker-compose.
    
    Returns:
        Tuple of (port_assignments, ports_yaml_snippet)
    """
    port_assignments = assign_ports(services)
    
    # Store port info for later display
    return port_assignments


def check_and_report_ports(services: Dict[str, str]) -> Dict[str, int]:
    """
    Check ports, assign available ones, and report to user.
    
    Args:
        services: Dict of service_name -> service_type
        
    Returns:
        Dict of service_name -> assigned_port
    """
    console.print("\n[bold cyan]🔍 Checking port availability...[/]")
    
    assignments = {}
    conflicts = []
    
    for service_name, service_type in services.items():
        default_port = DEFAULT_PORTS.get(service_type.lower(), 8000)
        
        if is_port_available(default_port):
            assignments[service_name] = default_port
            console.print(f"  [green]✓[/] {service_name}: Port {default_port} available")
        else:
            # Find alternative
            new_port = find_available_port(service_type, default_port + 1)
            assignments[service_name] = new_port
            conflicts.append((service_name, default_port, new_port))
            console.print(f"  [yellow]⚠[/] {service_name}: Port {default_port} in use → using {new_port}")
    
    if conflicts:
        console.print(f"\n[yellow]Note: {len(conflicts)} port(s) were reassigned due to conflicts[/]")
    
    return assignments
