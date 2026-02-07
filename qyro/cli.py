"""
Qyro CLI - Modern SaaS Edition
Beautiful, animated terminal interface for the polyglot runtime.
"""

import typer
import time
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.style import Style
from rich import box
from rich.markdown import Markdown
from rich.syntax import Syntax

from qyro.core.orchestrator import Orchestrator

app = typer.Typer(
    help="🌀 Qyro: The Universal Polyglot Runtime",
    no_args_is_help=False,
    add_completion=False
)
console = Console()

# Modern SaaS color palette
COLORS = {
    "primary": "#6366f1",      # Indigo
    "secondary": "#8b5cf6",    # Violet
    "success": "#22c55e",      # Green
    "warning": "#f59e0b",      # Amber
    "error": "#ef4444",        # Red
    "info": "#3b82f6",         # Blue
    "muted": "#64748b",        # Slate
    "accent": "#06b6d4",       # Cyan
}


def print_banner(animate: bool = True):
    """Print animated Qyro banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗ ██╗   ██╗██████╗  ██████╗                          ║
║  ██╔═══██╗╚██╗ ██╔╝██╔══██╗██╔═══██╗                         ║
║  ██║   ██║ ╚████╔╝ ██████╔╝██║   ██║                         ║
║  ██║▄▄ ██║  ╚██╔╝  ██╔══██╗██║   ██║                         ║
║  ╚██████╔╝   ██║   ██║  ██║╚██████╔╝                         ║
║   ╚══▀▀═╝    ╚═╝   ╚═╝  ╚═╝ ╚═════╝                          ║
║                                                               ║
║         Universal Polyglot Runtime • v3.0                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    if animate:
        lines = banner.split('\n')
        for i, line in enumerate(lines):
            if i < 3 or i > len(lines) - 3:
                console.print(line, style=f"bold {COLORS['muted']}")
            else:
                console.print(line, style=f"bold {COLORS['primary']}")
            time.sleep(0.02)
    else:
        console.print(banner, style=f"bold {COLORS['primary']}")


def print_status(message: str, status: str = "info"):
    """Print a styled status message."""
    icons = {
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "info": "ℹ",
        "running": "●",
    }
    icon = icons.get(status, "•")
    color = COLORS.get(status, COLORS["info"])
    console.print(f"  [{color}]{icon}[/] {message}")


def create_services_table(services) -> Table:
    """Create a styled services table."""
    table = Table(
        box=box.ROUNDED,
        border_style=COLORS["muted"],
        header_style=f"bold {COLORS['primary']}",
        title="[bold]Generated Services[/]",
        title_style=COLORS["primary"]
    )
    table.add_column("Service", style="bold white")
    table.add_column("Language", style=COLORS["accent"])
    table.add_column("Dependencies", style=COLORS["muted"])
    table.add_column("Status", justify="center")
    
    for service in services:
        deps = ", ".join(service.dependencies[:3]) if service.dependencies else "—"
        if len(service.dependencies) > 3:
            deps += f" +{len(service.dependencies) - 3} more"
        table.add_row(
            service.name,
            service.language,
            deps,
            f"[{COLORS['success']}]Ready[/]"
        )
    
    return table


def validate_file_path(file_path: str) -> Path:
    """Validate that the file exists and has .qyro extension."""
    path = Path(file_path)
    
    if not path.exists():
        raise typer.BadParameter(f"File not found: {file_path}")
    
    if path.suffix != ".qyro":
        raise typer.BadParameter(f"File must have .qyro extension: {file_path}")
    
    return path


def validate_project_directory():
    """Validate that we're in a valid Qyro project directory."""
    compose_file = Path("docker-compose.yml")
    
    if not compose_file.exists():
        qyro_files = list(Path(".").glob("*.qyro"))
        if qyro_files:
            raise typer.BadParameter(
                "No docker-compose.yml found. Run 'qyro setup' first."
            )
        else:
            raise typer.BadParameter(
                "No Qyro project found. Run 'qyro init <name>' to create one."
            )


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    🌀 Qyro - Universal Polyglot Runtime
    
    Build microservices in Python, Rust, Java, and Node.js in a single file.
    """
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print()
        
        # Show interactive menu
        console.print(Panel(
            "[bold]Quick Start[/]\n\n"
            f"  [{COLORS['primary']}]qyro init <name>[/]     Create a new project\n"
            f"  [{COLORS['primary']}]qyro run <file>[/]      Run a .qyro file\n"
            f"  [{COLORS['primary']}]qyro setup[/]           Generate Docker artifacts\n"
            f"  [{COLORS['primary']}]qyro start[/]           Start containers\n"
            f"  [{COLORS['primary']}]qyro stop[/]            Stop containers\n"
            f"  [{COLORS['primary']}]qyro logs[/]            Stream service logs\n"
            f"  [{COLORS['primary']}]qyro status[/]          Check service status\n",
            title="[bold]Commands[/]",
            border_style=COLORS["muted"],
            padding=(1, 2)
        ))


@app.command()
def init(name: str = typer.Argument(..., help="Name of the project")):
    """Initialize a new Qyro project with sample code."""
    print_banner(animate=False)
    console.print()
    
    with Progress(
        SpinnerColumn(style=COLORS["primary"]),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Creating project [bold]{name}[/]...", total=None)
        
        path = Path(name)
        path.mkdir(exist_ok=True)
        
        # Create sample .qyro file
        sample_content = f'''# {name} - Qyro Polyglot Application
# Run with: qyro run {name}.qyro

>>>python:api [fastapi, uvicorn]
from fastapi import FastAPI
import sys
sys.path.insert(0, '/app/qyro_adapters')
from python_adapter import set, get, expose, info

app = FastAPI(title="{name} API")

@expose
def hello(name: str) -> str:
    """Say hello - callable from any language!"""
    return f"Hello, {{name}}!"

@app.get("/")
def root():
    count = get("visits") or 0
    set("visits", int(count) + 1)
    return {{"message": "Welcome to {name}!", "visits": count + 1}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

>>>web:frontend [react]
import React, {{ useState, useEffect }} from 'react';
import axios from 'axios';

function App() {{
  const [data, setData] = useState(null);
  
  useEffect(() => {{
    axios.get('http://localhost:8000/')
      .then(r => setData(r.data))
      .catch(console.error);
  }}, []);

  return (
    <div style={{{{textAlign:'center',marginTop:100,fontFamily:'system-ui'}}}}>
      <h1>🌀 {name}</h1>
      <p>{{data ? `Visits: ${{data.visits}}` : 'Loading...'}}</p>
    </div>
  );
}}
export default App;
'''
        (path / f"{name}.qyro").write_text(sample_content)
        
        time.sleep(0.5)
        progress.update(task, completed=True)
    
    console.print()
    print_status(f"Created project directory: [bold]{name}/[/]", "success")
    print_status(f"Created file: [bold]{name}/{name}.qyro[/]", "success")
    console.print()
    
    console.print(Panel(
        f"[bold]Next Steps[/]\n\n"
        f"  1. cd {name}\n"
        f"  2. qyro run {name}.qyro\n",
        border_style=COLORS["success"],
        padding=(1, 2)
    ))


@app.command()
def setup(
    file: str = typer.Argument(None, help="The .qyro file to process")
):
    """Parse .qyro file and generate Docker artifacts."""
    print_banner(animate=False)
    console.print()

    try:
        with Progress(
            SpinnerColumn(style=COLORS["primary"]),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style=COLORS["primary"], finished_style=COLORS["success"]),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Initializing...", total=4)
            
            progress.update(task, description="Parsing .qyro file...")
            orchestrator = Orchestrator(file)
            services = orchestrator.parse_and_generate_artifacts()
            progress.advance(task)
            
            progress.update(task, description="Resolving dependencies...")
            orchestrator.resolve_dependencies()
            progress.advance(task)
            
            progress.update(task, description="Generating Dockerfiles...")
            time.sleep(0.3)
            progress.advance(task)
            
            progress.update(task, description="Creating docker-compose.yml...")
            time.sleep(0.2)
            progress.advance(task)
        
        console.print()
        console.print(create_services_table(services))
        console.print()
        print_status("Setup complete! Artifacts generated.", "success")
        
    except FileNotFoundError as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)
    except Exception as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)


@app.command()
def start(
    detach: bool = typer.Option(True, "--detach", "-d", help="Run in background"),
    file: str = typer.Option(None, "--file", "-f", help="The .qyro file to use"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Do not use cache when building")
):
    """Start the Docker containers."""
    print_banner(animate=False)
    console.print()

    try:
        if not Path("docker-compose.yml").exists():
            print_status("No artifacts found. Running setup first...", "warning")
            console.print()
            
            orchestrator = Orchestrator(file)
            orchestrator.parse_and_generate_artifacts()
            orchestrator.resolve_dependencies()
            orchestrator.ensure_base_images()
            orchestrator.start_services(detach=detach, no_cache=no_cache)
        else:
            orchestrator = Orchestrator(file)
            orchestrator.ensure_base_images()
            orchestrator.start_services(detach=detach, no_cache=no_cache)
            
    except FileNotFoundError as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)
    except Exception as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)


@app.command()
def stop():
    """Stop all Docker containers."""
    print_banner(animate=False)
    console.print()

    try:
        validate_project_directory()
        
        with Progress(
            SpinnerColumn(style=COLORS["warning"]),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Stopping services...", total=None)
            
            orchestrator = Orchestrator()
            orchestrator.stop_services()
            
            progress.update(task, completed=True)
        
        console.print()
        print_status("All services stopped.", "success")
        
    except typer.BadParameter as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)
    except Exception as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)


@app.command()
def logs(
    service: str = typer.Option(None, "--service", "-s", help="Specific service"),
    follow: bool = typer.Option(True, "--follow", "-f", help="Follow output"),
    tail: int = typer.Option(100, "--tail", help="Lines from end")
):
    """Stream logs from services."""
    print_banner(animate=False)
    console.print()

    try:
        validate_project_directory()
        orchestrator = Orchestrator()
        
        if service:
            print_status(f"Streaming logs for: [bold]{service}[/]", "info")
        else:
            print_status("Streaming logs from all services...", "info")
        
        console.print(f"  [{COLORS['muted']}]Press Ctrl+C to stop[/]")
        console.print()
        
        orchestrator.stream_logs(service=service, follow=follow, tail=tail)
        
    except typer.BadParameter as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)
    except Exception as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)


@app.command()
def status():
    """Check the status of all services."""
    print_banner(animate=False)
    console.print()

    try:
        validate_project_directory()
        orchestrator = Orchestrator()
        orchestrator.check_service_status()
        
    except typer.BadParameter as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)
    except Exception as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)


@app.command()
def build(
    file: str = typer.Argument(None, help="The .qyro file to build"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Do not use cache when building"),
    prod: bool = typer.Option(False, "--prod", help="Use production optimization")
):
    """Build the application services."""
    print_banner(animate=False)
    console.print()

    try:
        with Progress(
            SpinnerColumn(style=COLORS["primary"]),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Building services...", total=None)
            
            orchestrator = Orchestrator(file)
            
            progress.update(task, description="Parsing .qyro file...")
            orchestrator.parse_and_generate_artifacts(prod=prod)
            
            progress.update(task, description="Resolving dependencies...")
            orchestrator.resolve_dependencies()
            
            progress.update(task, description="Building images...")
            orchestrator.ensure_base_images()
            
            # Explicit build
            orchestrator.build_services(no_cache=no_cache)
            
        console.print()
        print_status("Build complete!", "success")
        
    except FileNotFoundError as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)
    except Exception as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)


@app.command()
def run(
    file: str = typer.Argument(None, help="The .qyro file to run"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Do not use cache when building"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch for changes and hot reload")
):
    """Setup and run in one command (recommended)."""
    print_banner()
    console.print()

    try:
        with Progress(
            SpinnerColumn(style=COLORS["primary"]),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Starting Qyro...", total=None)
            
            orchestrator = Orchestrator(file)
            
            progress.update(task, description="Parsing .qyro file...")
            orchestrator.parse_and_generate_artifacts()
            
            progress.update(task, description="Resolving dependencies...")
            orchestrator.resolve_dependencies()
            
            progress.update(task, description="Building images...")
            orchestrator.ensure_base_images()
            
            progress.update(task, description="Starting services...")
            orchestrator.start_services(detach=True, no_cache=no_cache)
        
        console.print()
        print_status("All services running!", "success")
        console.print()
        
        console.print(Panel(
            f"[bold]Services Ready![/]\n\n"
            f"  • API: http://localhost:8000\n"
            f"  • Frontend: http://localhost:3000\n"
            f"  • Redis: localhost:6379\n"
            f"  • Kafka: localhost:9092\n",
            title="[bold green]🚀 Running[/]",
            border_style=COLORS["success"],
            padding=(1, 2)
        ))
        
        if watch:
            print_status("Watching for changes... (Press Ctrl+C to stop)", "info")
            orchestrator.start_watching()
        else:
            print_status("Press Ctrl+C to stop logs...", "info")
            console.print()
            orchestrator.stream_logs()
        
    except FileNotFoundError as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print()
        print_status("Stopped log streaming. Services still running.", "warning")
        print_status("Run 'qyro stop' to stop all services.", "info")
    except Exception as e:
        print_status(str(e), "error")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show Qyro version information."""
    import importlib.metadata
    try:
        ver = importlib.metadata.version("qyro")
        console.print(f"\n  [bold {COLORS['primary']}]QYRO[/] v{ver}")
        console.print(f"  Universal Polyglot Runtime\n")
    except Exception:
        console.print(f"\n  [bold {COLORS['primary']}]QYRO[/] v3.0.0")
        console.print(f"  Universal Polyglot Runtime\n")


if __name__ == "__main__":
    app()
