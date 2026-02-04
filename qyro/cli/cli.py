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
def run(qyro_file, detach, rebuild):
    """Run the application using Docker with a premium dashboard."""
    dist_dir = Path("qyro_dist")
    compose_file = dist_dir / "docker-compose.yml"

    if not compose_file.exists():
        if qyro_file:
            console.print("[yellow]Build context not found. Running setup...[/yellow]")
            ctx = click.get_current_context()
            ctx.invoke(setup, qyro_file=qyro_file)
        else:
            console.print("[red]Error: No build context found. Run 'qyro setup <file>' first.[/red]")
            sys.exit(1)

    dashboard = QyroDashboard(str(compose_file))

    try:
        # Start Docker Compose
        console.print("[bold green]Starting services...[/bold green]")
        cmd = ["docker-compose", "-f", str(compose_file), "up", "-d"]
        if rebuild: cmd.append("--build")

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if detach:
            console.print("[green]Services started in background.[/green]")
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

                layout["main"]["logs"].update(dashboard.generate_logs_panel())
                time.sleep(0.5)

    except KeyboardInterrupt:
        console.print("[yellow]Stopping services...[/yellow]")
        subprocess.run(["docker-compose", "-f", str(compose_file), "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
