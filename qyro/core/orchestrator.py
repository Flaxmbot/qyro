import os
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from qyro.core.parser import QyroParser, ServiceBlock
from qyro.core.docker_manager import DockerManager
from qyro.core.templates import DOCKER_COMPOSE_TEMPLATE
import qyro.lib

console = Console()

class Orchestrator:
    """
    Orchestrates the Qyro runtime by managing the lifecycle of language-specific containers.
    Handles artifact generation, container lifecycle management, and dependency resolution.
    """
    
    def __init__(self, qyro_file: Optional[str] = None):
        """
        Initialize the orchestrator.
        
        Args:
            qyro_file: Path to the .qyro file to orchestrate. If None, will search current directory.
        """
        self.qyro_file = self._resolve_qyro_file(qyro_file)
        self.parser = QyroParser(self.qyro_file)
        self.services: List[ServiceBlock] = []
        self.project_root = self.qyro_file.parent
        self.docker_manager = DockerManager()
        
    def _resolve_qyro_file(self, qyro_file: Optional[str]) -> Path:
        """Resolve the path to the .qyro file."""
        if qyro_file is not None:
            path = Path(qyro_file)
            if not path.exists():
                raise FileNotFoundError(f"Qyro file not found: {qyro_file}")
            return path
        
        # Search for .qyro files in current directory
        qyro_files = list(Path(".").glob("*.qyro"))
        if not qyro_files:
            raise FileNotFoundError("No .qyro files found in current directory")
        elif len(qyro_files) > 1:
            raise Exception("Multiple .qyro files found. Please specify which one to use.")
        
        return qyro_files[0]
    
    def parse_and_generate_artifacts(self, prod: bool = False) -> List[ServiceBlock]:
        """Parse the .qyro file and generate language-specific artifacts."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task1 = progress.add_task("Parsing Qyro file...", total=1)
            self.services = self.parser.parse()
            progress.update(task1, completed=1)
            
            task2 = progress.add_task("Generating language-specific artifacts...", total=1)
            services_config = self.parser.generate_artifacts(self.project_root, prod=prod)
            progress.update(task2, completed=1)
            
            task3 = progress.add_task("Creating docker-compose.yml...", total=1)
            compose_content = DOCKER_COMPOSE_TEMPLATE.format(services="".join(services_config))
            (self.project_root / "docker-compose.yml").write_text(compose_content)
            progress.update(task3, completed=1)
            
        console.print("[bold green]✓ Artifact generation complete[/]")
        return self.services
    
    def resolve_dependencies(self) -> List[str]:
        """Resolve service dependencies and determine startup order."""
        # Create dependency graph
        dependency_graph: Dict[str, List[str]] = {}
        for service in self.services:
            dependency_graph[service.name] = service.dependencies
            
        # Topological sort to determine startup order
        visited = set()
        order = []
        
        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for dep in dependency_graph.get(node, []):
                if dep in dependency_graph:  # Only process known services as dependencies
                    dfs(dep)
            order.append(node)
            
        for service in self.services:
            dfs(service.name)
            
        console.print(f"[dim]Dependency resolution complete. Startup order: {', '.join(order)}[/]")
        return order
    
    def ensure_base_images(self):
        """Ensure language-specific base images are built or available."""
        if not self.docker_manager.ensure_docker_running():
            raise Exception("Docker is not running")
            
        # Build base images with shared layers
        adapter_path = Path(qyro.lib.__file__).parent
        if not self.docker_manager.build_base_images(adapter_path):
            raise Exception("Failed to build base images")
            
        console.print("[bold green]✓ Base images ready[/]")
    
    def build_services(self, no_cache: bool = False):
        """Build the application services."""
        # Change to project directory
        original_dir = os.getcwd()
        os.chdir(self.project_root)
        try:
            return self.docker_manager.build_services(no_cache=no_cache)
        finally:
            os.chdir(original_dir)

    def start_services(self, detach: bool = True, no_cache: bool = False):
        """Start all services in the correct order."""
        # Change to project directory to run docker-compose
        original_dir = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            # If no_cache is requested, build explicitly first
            if no_cache:
                console.print("[bold yellow]Rebuilding dependencies with --no-cache...[/]")
                if not self.docker_manager.build_services(no_cache=True):
                    raise Exception("Failed to build services")
                    
            console.print(f"[blue]Starting services from: {self.project_root}[/]")
            
            # Start services (skip implicit build if we just built it)
            if not self.docker_manager.run_compose(detach=detach, build=not no_cache):
                raise Exception("Failed to start services")
                
            if detach:
                console.print("[green]Containers running in background[/]")
                # Display service URLs
                self._display_service_urls()
            else:
                self.docker_manager.stream_logs()
                
        finally:
            os.chdir(original_dir)
    
    def _display_service_urls(self):
        """Display service URLs after startup."""
        import subprocess
        import re
        
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}:{{.Ports}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                from rich.table import Table
                table = Table(title="🚀 Service URLs", show_header=True, header_style="bold cyan")
                table.add_column("Service", style="bold")
                table.add_column("URL", style="green")
                table.add_column("Status", style="bold green")
                
                for line in result.stdout.strip().split('\n'):
                    if ':' in line and line.strip():
                        parts = line.split(':', 1)
                        name = parts[0]
                        ports = parts[1] if len(parts) > 1 else ""
                        
                        # Parse the port mapping (e.g., "0.0.0.0:3000->3000/tcp")
                        port_match = re.search(r'0\.0\.0\.0:(\d+)->', ports)
                        if port_match:
                            port = port_match.group(1)
                            url = f"http://localhost:{port}"
                            table.add_row(name, url, "✅ Running")
                
                if table.row_count > 0:
                    console.print()
                    console.print(table)
                    console.print()
        except Exception:
            pass  # Silently fail if we can't get port info
            
    def stop_services(self):
        """Stop all running services."""
        original_dir = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            console.print("[blue]Stopping services...[/]")
            cmd = ["docker-compose", "down"]
            
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print("[green]✓ Services stopped successfully[/]")
            else:
                console.print(f"[red]✗ Error stopping services:[/] {result.stderr}")
                raise Exception(f"Failed to stop services: {result.stderr}")
                
        finally:
            os.chdir(original_dir)
            
    def start_watching(self):
        """Start watching for changes and reload services."""
        from qyro.core.watcher import QyroWatcher
        
        def _on_file_changed():
            console.print(f"\n[bold yellow]🔄 Detected change in {self.qyro_file.name}. Reloading...[/]")
            try:
                # Re-parse and regenerate
                self.parse_and_generate_artifacts()
                self.resolve_dependencies()
                
                # Check if we need to rebuild base images? Maybe not for simple code changes.
                # Just restart services with build
                console.print("[dim]Updating running services...[/]")
                if not self.docker_manager.run_compose(detach=True, build=True):
                    console.print("[red]Failed to restart services[/]")
                else:
                    console.print("[bold green]✅ Reload complete![/]")
                    # Update displayed URLs in case ports changed
                    self._display_service_urls()
                    
            except Exception as e:
                console.print(f"[bold red]✗ Error reloading:[/bold red] {e}")

        # Start watcher
        watcher = QyroWatcher(self.qyro_file, _on_file_changed)
        watcher.start()
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            watcher.stop()
            console.print("\n[yellow]Stopping watcher...[/]")

    def stream_logs(self, service: str = None, follow: bool = True, tail: int = 100):
        """Stream logs from services."""
        original_dir = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            self.docker_manager.stream_logs(service=service, follow=follow, tail=tail)
        finally:
            os.chdir(original_dir)
            
    def check_service_status(self):
        """Check the status of all services."""
        original_dir = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            cmd = ["docker-compose", "ps"]
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print("[bold blue]Service Status:[/]")
                console.print(result.stdout)
            else:
                console.print(f"[red]✗ Error checking status:[/] {result.stderr}")
                raise Exception(f"Failed to check status: {result.stderr}")
                
        finally:
            os.chdir(original_dir)
            
    def run_full_workflow(self, detach: bool = True):
        """Run the full orchestration workflow: parse, generate, start."""
        try:
            # Parse and generate artifacts
            self.parse_and_generate_artifacts()
            
            # Resolve dependencies
            self.resolve_dependencies()
            
            # Ensure base images are available
            self.ensure_base_images()
            
            # Start services
            self.start_services(detach=detach)
            
            # Stream logs if not detached
            if not detach:
                self.stream_logs()
                
            return True
            
        except Exception as e:
            console.print(f"[bold red]✗ Orchestration failed:[/] {e}")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/]")
            return False
