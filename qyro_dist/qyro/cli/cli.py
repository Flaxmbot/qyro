"""
Qyro Command Line Interface
"""

import sys
import os
import click
import subprocess
import time
import threading
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.ansi import AnsiDecoder
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import pyfiglet
import docker
from datetime import datetime

try:
    from qyro.common.parser import QyroParser
    from qyro.common.docker_builder import QyroDockerBuilder
    from qyro.orchestrator.orchestrator import QyroOrchestrator
    from qyro.common.config import QyroConfig
except ImportError:
    # Fallback
    sys.path.insert(0, os.getcwd())
    from qyro.common.parser import QyroParser
    from qyro.common.docker_builder import QyroDockerBuilder
    from qyro.orchestrator.orchestrator import QyroOrchestrator
    from qyro.common.config import QyroConfig

console = Console()

class QyroDashboard:
    def __init__(self, compose_file):
        self.client = docker.from_env()
        self.compose_file = compose_file
        self.project_name = Path(os.getcwd()).name.lower().replace(" ", "") + "_qyro" # Approximation
        # Actually docker-compose uses directory name by default.
        # But we can find containers by label com.docker.compose.project
        self.containers = {}
        self.logs = []
        self.lock = threading.Lock()
        self.decoder = AnsiDecoder()

    def get_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="services", ratio=1),
            Layout(name="logs", ratio=2)
        )
        return layout

    def generate_header(self):
        ascii_art = pyfiglet.figlet_format("QYRO", font="slant")
        return Panel(
            Text("Universal Polyglot Runtime", justify="center", style="bold white"),
            title=f"[bold cyan]QYRO CLI v2.0[/bold cyan]",
            border_style="cyan",
            padding=(0, 1)
        )

    def generate_services_table(self):
        table = Table(expand=True, border_style="dim")
        table.add_column("Service", style="bold cyan")
        table.add_column("State", style="white")
        table.add_column("Status", style="dim")

        for name, container in self.containers.items():
            state_style = "green" if container.status == "running" else "red"
            table.add_row(
                name,
                f"[{state_style}]{container.status.upper()}[/{state_style}]",
                container.attrs['State']['Status']
            )
        return Panel(table, title="Services", border_style="blue")

    def generate_logs_panel(self):
        return Panel(
            Text("\n".join(self.logs[-20:]), style="white"), # Show last 20 lines
            title="Real-time Logs",
            border_style="white"
        )

    def generate_footer(self):
        return Panel(
            Text("Press Ctrl+C to stop | Running in Docker mode", justify="center", style="dim"),
            style="on black"
        )
    
    def get_access_links(self) -> str:
        """Generate access links for running services."""
        links = []
        for name, container in self.containers.items():
            if container.status == "running":
                # Get ports
                ports = container.ports
                if ports:
                    for port_mapping in ports.values():
                        if port_mapping:
                            host_port = port_mapping[0].get('HostPort', '')
                            if host_port:
                                if name == 'qyro-app' or 'app' in name.lower():
                                    links.append(f"http://localhost:{host_port}")
        return "\n".join(links)

    def update_containers(self):
        # Find containers related to this project
        # Using a broad filter for now
        all_containers = self.client.containers.list(all=True)
        # Filter by name or labels if possible.
        # Since we use docker-compose, we can look for labels.
        # But for simplicity, we'll list all containers started by the compose file
        # We can just look for names containing 'qyro' or redis/kafka if we are sure.

        # Better: Filter by project directory name which compose uses as prefix
        prefix = os.path.basename(os.getcwd()).lower().replace("_", "").replace("-", "")

        for c in all_containers:
            # Check labels
            labels = c.labels
            project = labels.get('com.docker.compose.project')
            if project and (project == prefix or project == "qyro_dist"): # qyro_dist is where compose file is
                name = labels.get('com.docker.compose.service', c.name)
                self.containers[name] = c

    def stream_logs(self):
        # Stream logs from containers in background
        # This is complex with multiple containers.
        # For PoC, we might just poll logs or show status.
        pass

    def add_log(self, message):
        with self.lock:
            self.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            if len(self.logs) > 100:
                self.logs.pop(0)

@click.group()
def main():
    """Qyro - Universal Polyglot Runtime"""
    pass

@main.command()
@click.argument('qyro_file', type=click.Path(exists=True))
def setup(qyro_file):
    """Generate Docker configuration."""
    console.print(Panel(Text("Initializing Setup...", style="bold magenta"), border_style="magenta"))
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task1 = progress.add_task("[cyan]Parsing Qyro file...", total=1)
            parser = QyroParser()
            parser.parse_file(qyro_file)
            progress.update(task1, completed=1)

            task2 = progress.add_task("[cyan]Generating Docker build context...", total=1)
            builder = QyroDockerBuilder(qyro_file)
            builder.build(parser.get_named_blocks())
            progress.update(task2, completed=1)

        console.print(f"[bold green]Setup complete! Run 'qyro run {qyro_file}' to start.[/bold green]")
    except Exception as e:
        console.print(f"[red]Setup failed: {e}[/red]")
        sys.exit(1)

@main.command()
@click.argument('qyro_file', required=False)
@click.option('--detach', '-d', is_flag=True, help="Run in background")
@click.option('--rebuild', is_flag=True, help="Force rebuild")
@click.option('--local', '-l', is_flag=True, help="Run locally without Docker (for testing)")
def run(qyro_file, detach, rebuild, local):
    """Run the application using Docker or locally."""
    dist_dir = Path("qyro_dist")
    compose_file = dist_dir / "docker-compose.yml"
    
    # If local mode or no compose file, run directly with orchestrator
    if local or not compose_file.exists():
        if not qyro_file:
            # Auto-detect .qyro file
            import glob
            qyro_files = glob.glob("*.qyro")
            if qyro_files:
                qyro_file = qyro_files[0]
            else:
                console.print("[red]Error: No .qyro file found in current directory.[/red]")
                sys.exit(1)
        
        console.print(f"[bold green]Running {qyro_file} locally...[/bold green]")
        try:
            # Disable Redis/Kafka for local mode - use_services=False for local testing
            config = QyroConfig(
                redis_host="localhost",
                redis_port=6379,
                kafka_bootstrap_servers=os.environ.get("QYRO_KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
            )
            # Pass use_services=False to run without Redis/Kafka dependencies
            orchestrator = QyroOrchestrator(qyro_file, config, skip_missing=True, use_services=False)
            orchestrator.start()
        except KeyboardInterrupt:
            console.print("[yellow]Stopped by user.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error running locally: {e}[/red]")
            sys.exit(1)
        return
    
    # Docker mode
    dashboard = QyroDashboard(str(compose_file))

    try:
        # Check if containers are already running
        console.print("[bold green]Checking container status...[/bold green]")
        
        ps_cmd = ["docker-compose", "-f", str(compose_file), "ps"]
        console.print(f"[dim]Running: {' '.join(ps_cmd)}[/dim]")
        
        status_result = subprocess.run(
            ps_cmd,
            capture_output=True,
            text=True
        )
        
        # Show output so user can see what's happening
        if status_result.stdout:
            console.print(f"[dim]Container status:\n{status_result.stdout}[/dim]")
        if status_result.stderr:
            console.print(f"[yellow]Status stderr: {status_result.stderr}[/yellow]")
        
        # Improved container detection - handles more states
        running_containers = []
        if status_result.returncode == 0:
            for line in status_result.stdout.split('\n'):
                line = line.strip()
                if not line or line.startswith('--'):
                    continue
                # Check for various running states
                if any(state in line for state in ['Up', 'running', 'Up (healthy)']):
                    parts = line.split()
                    if parts:
                        # Get container name (first column)
                        container_name = parts[0]
                        # Skip header-like entries
                        if container_name not in ['Name', 'Container']:
                            running_containers.append(container_name)
        
        console.print(f"[dim]Detected running containers: {running_containers}[/dim]")
        
        # If containers are running, use them
        if running_containers:
            console.print(f"[green]✓ Found {len(running_containers)} existing containers running. Using them...[/green]")
            if detach:
                console.print("[green]✓ Services already running in background.[/green]")
                return
        else:
            # No running containers, need to start them
            console.print("[yellow]⚠ No running containers found. Starting services...[/yellow]")
            
            # Clean up stale containers (removed -v flag to avoid data loss)
            console.print("[bold green]Cleaning up stale containers...[/bold green]")
            
            cleanup_cmd = ["docker-compose", "-f", str(compose_file), "down", "--remove-orphans"]
            console.print(f"[dim]Running: {' '.join(cleanup_cmd)}[/dim]")
            
            # Show cleanup output to user
            cleanup_result = subprocess.run(
                cleanup_cmd,
                capture_output=True,
                text=True
            )
            if cleanup_result.stdout:
                console.print(f"[dim]{cleanup_result.stdout}[/dim]")
            if cleanup_result.stderr:
                console.print(f"[yellow]{cleanup_result.stderr}[/yellow]")
            
            # Build the docker-compose up command
            cmd = ["docker-compose", "-f", str(compose_file), "up", "-d"]
            if rebuild:
                cmd.append("--build")

            console.print(f"[bold cyan]► Running: {' '.join(cmd)}[/bold cyan]")
            console.print("[yellow]Starting containers (this may take a minute)...[/yellow]")
            
            # Run with output visible to user
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Show output to user
            if result.stdout:
                console.print(f"[dim]{result.stdout}[/dim]")
            if result.stderr:
                console.print(f"[yellow]{result.stderr}[/yellow]")
            
            if result.returncode != 0:
                stderr = result.stderr
                # Check for container name conflict
                if "already in use" in stderr or "Conflict" in stderr:
                    console.print("[yellow]⚠ Container conflict detected. Force removing...[/yellow]")
                    # Force remove specific containers
                    force_rm_cmd = ["docker", "rm", "-f", "qyro-redis", "qyro-kafka", "qyro-zookeeper", "qyro_dist-qyro-app-1"]
                    console.print(f"[dim]Running: {' '.join(force_rm_cmd)}[/dim]")
                    subprocess.run(force_rm_cmd, capture_output=True)
                    
                    # Retry starting
                    console.print(f"[bold cyan]► Retrying: {' '.join(cmd)}[/bold cyan]")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        console.print(f"[red]✗ Docker compose failed: {result.stderr}[/red]")
                        console.print("[yellow]Trying alternative approach without health checks...[/yellow]")
                        subprocess.run(["docker-compose", "-f", str(compose_file), "down"], capture_output=True)
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode != 0:
                            console.print(f"[red]✗ Docker compose failed: {result.stderr}[/red]")
                            console.print("[yellow]Try running with --local flag: qyro run chat_app.qyro --local[/yellow]")
                            sys.exit(1)
                elif "unhealthy" in stderr:
                    console.print("[yellow]⚠ Container health check failed. Restarting...[/yellow]")
                    subprocess.run(["docker-compose", "-f", str(compose_file), "down"], capture_output=True)
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        console.print(f"[red]✗ Docker compose failed: {result.stderr}[/red]")
                        console.print("[yellow]Try running with --local flag: qyro run chat_app.qyro --local[/yellow]")
                        sys.exit(1)
                else:
                    console.print(f"[red]✗ Docker compose failed: {result.stderr}[/red]")
                    console.print("[yellow]Try running with --local flag: qyro run chat_app.qyro --local[/yellow]")
                    sys.exit(1)
            
            # Wait for containers and show progress
            console.print("[yellow]⏳ Waiting for services to start...[/yellow]")
            
            # Poll with progress indication
            max_wait = 60
            waited = 0
            while waited < max_wait:
                ps_result = subprocess.run(
                    ["docker-compose", "-f", str(compose_file), "ps", "qyro-app"],
                    capture_output=True, text=True
                )
                if ps_result.returncode == 0 and "Up" in ps_result.stdout:
                    console.print("[green]✓ Container is up! Checking health...[/green]")
                    break
                time.sleep(2)
                waited += 2
                console.print(f"[dim]Waited {waited}s...[/dim]")
            
            # Show final status
            console.print("[green]✓ Services started successfully![/green]")
            
            # Show running containers
            subprocess.run(["docker-compose", "-f", str(compose_file), "ps"])

        if detach:
            console.print("[green]✓ Services started in background.[/green]")
            return

        # Start Dashboard Loop
        layout = dashboard.get_layout()
        layout["header"].update(dashboard.generate_header())
        layout["footer"].update(dashboard.generate_footer())

        with Live(layout, refresh_per_second=4, screen=True) as live:
            while True:
                dashboard.update_containers()
                layout["main"]["services"].update(dashboard.generate_services_table())

                # Fetch recent logs from orchestrator
                if 'qyro-app' in dashboard.containers:
                    try:
                        logs = dashboard.containers['qyro-app'].logs(tail=10).decode('utf-8')
                        dashboard.logs = logs.split('\n')
                    except: pass
                
                # Show access links prominently
                links = dashboard.get_access_links()
                if links:
                    dashboard.logs.insert(0, f"[green]>>> ACCESS LINKS: {links}[/green]")

                layout["main"]["logs"].update(dashboard.generate_logs_panel())
                time.sleep(0.5)

    except KeyboardInterrupt:
        console.print("[yellow]Stopping services...[/yellow]")
        subprocess.run(["docker-compose", "-f", str(compose_file), "down"])
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

@main.command()
def stop():
    """Stop running services."""
    dist_dir = Path("qyro_dist")
    compose_file = dist_dir / "docker-compose.yml"
    if compose_file.exists():
        console.print("[yellow]Stopping services...[/yellow]")
        subprocess.run(["docker-compose", "-f", str(compose_file), "down"])
        console.print("[green]Services stopped.[/green]")
    else:
        console.print("[red]No active configuration found.[/red]")

@main.command()
def status():
    """Show status of services."""
    dist_dir = Path("qyro_dist")
    compose_file = dist_dir / "docker-compose.yml"
    if compose_file.exists():
        subprocess.run(["docker-compose", "-f", str(compose_file), "ps"])
    else:
        console.print("[red]No active configuration found.[/red]")

@main.command(hidden=True)
@click.argument('qyro_file', required=False)
def run_internal(qyro_file):
    """Internal entrypoint for Docker container."""
    try:
        if not qyro_file:
             import glob
             files = glob.glob("*.qyro")
             if files: qyro_file = files[0]

        if not qyro_file:
            console.print("[red]No .qyro file found to run.[/red]")
            sys.exit(1)

        console.print(f"[bold green]Starting Orchestrator for {qyro_file}...[/bold green]")

        config = QyroConfig(
            redis_host=os.environ.get("QYRO_REDIS_HOST", "redis"),
            redis_port=int(os.environ.get("QYRO_REDIS_PORT", 6379)),
            kafka_bootstrap_servers=os.environ.get("QYRO_KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        )

        orchestrator = QyroOrchestrator(qyro_file, config)
        orchestrator.start()

    except Exception as e:
        console.print(f"[red]Orchestrator failed: {e}[/red]")
        sys.exit(1)

@main.command()
def init():
    """Initialize a new project."""
    from .interactive import init_project
    init_project()

@main.command()
@click.argument('qyro_file', type=click.Path(exists=True))
@click.option('--k8s', is_flag=True, help="Generate Kubernetes manifests")
def deploy(qyro_file, k8s):
    """Deploy the application."""
    if k8s:
        try:
            from qyro.common.k8s_builder import QyroK8sBuilder
            from qyro.common.parser import QyroParser

            console.print(f"[bold green]Generating Kubernetes manifests for {qyro_file}...[/bold green]")

            parser = QyroParser()
            parser.parse_file(qyro_file)

            builder = QyroK8sBuilder(qyro_file)
            builder.build(parser.get_named_blocks())

        except Exception as e:
            console.print(f"[red]Deploy failed: {e}[/red]")
            sys.exit(1)
    else:
        console.print("[yellow]Please specify a deployment target (e.g. --k8s)[/yellow]")

if __name__ == "__main__":
    main()
