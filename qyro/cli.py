import typer
import time
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from pyfiglet import Figlet

from qyro.core.parser import QyroParser
from qyro.core.docker_manager import DockerManager
from qyro.core.templates import DOCKER_COMPOSE_TEMPLATE

app = typer.Typer(help="Qyro: The Minimalist Polyglot Runtime")
console = Console()

def print_banner():
    f = Figlet(font='slant')
    console.print(f.renderText('QYRO'), style="bold cyan")
    console.print(Panel("Universal Polyglot Runtime • SaaS Edition", border_style="cyan"))

@app.command()
def init(name: str = typer.Argument(..., help="Name of the project")):
    """Initialize a new Qyro project."""
    print_banner()
    console.print(f"[bold green]Creating new project: {name}[/]")

    path = Path(name)
    path.mkdir(exist_ok=True)

    # Create a sample .qyro file
    sample_content = """
>>>python:api [fastapi, uvicorn]
from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World", "Service": "Python"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

>>>web:frontend [react]
import React from 'react';

function App() {
  return (
    <div style={{textAlign: 'center', marginTop: '50px'}}>
      <h1>Hello from Qyro React!</h1>
    </div>
  );
}
export default App;
"""
    (path / f"{name}.qyro").write_text(sample_content)

    console.print(f"[green]✓[/] Created directory [bold]{name}[/]")
    console.print(f"[green]✓[/] Created file [bold]{name}/{name}.qyro[/]")
    console.print("\n[yellow]Run:[/yellow] [bold]cd {name} && qyro run {name}.qyro[/bold]")

@app.command()
def setup(file: str = typer.Argument(..., help="The .qyro file to process")):
    """Parse .qyro file and generate Docker artifacts."""
    print_banner()

    path = Path(file)
    if not path.exists():
        console.print(f"[bold red]Error:[/] File {file} not found.")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task1 = progress.add_task("Parsing Qyro file...", total=1)
        parser = QyroParser(file)
        parser.parse()
        progress.update(task1, completed=1)

        task2 = progress.add_task("Generating microservices...", total=1)
        # Generate artifacts in the same directory as the .qyro file
        # But we need a project root. Let's assume .qyro file is in the root or we create a build dir.
        # User said "make ecommerce folder using .qyro files".
        # If I run `qyro run ecommerce/ecommerce.qyro`, I should generate inside `ecommerce/`.

        project_root = path.parent
        services_config = parser.generate_artifacts(project_root)
        progress.update(task2, completed=1)

        task3 = progress.add_task("Creating docker-compose.yml...", total=1)
        compose_content = DOCKER_COMPOSE_TEMPLATE.format(services="".join(services_config))
        (project_root / "docker-compose.yml").write_text(compose_content)
        progress.update(task3, completed=1)

    console.print("[bold green]Setup complete![/] Artifacts generated.")

@app.command()
def start(
    detach: bool = typer.Option(True, "--detach", "-d", help="Run containers in background")
):
    """Start the Docker containers."""
    dm = DockerManager()
    if not dm.ensure_docker_running():
        raise typer.Exit(code=1)

    # Assume docker-compose.yml is in current dir
    # If not, we might need to find it. But usually we run this where we ran setup.
    if not Path("docker-compose.yml").exists():
        # Try to look in subdirectories? Or just fail.
        # Let's fail for now, strict clean code.
        console.print("[bold red]Error:[/] docker-compose.yml not found. Run 'qyro setup <file>' first.")
        raise typer.Exit(code=1)

    dm.run_compose(detach=detach)

    if detach:
        console.print("[green]Containers running in background.[/] Use 'docker-compose logs -f' to view logs.")
    else:
        dm.stream_logs()

@app.command()
def run(file: str = typer.Argument(..., help="The .qyro file to run")):
    """Setup and Start in one go."""
    # We need to change to the directory of the file potentially?
    # Or keep everything relative.
    # If I run `qyro run ecommerce/ecommerce.qyro`, artifacts go into `ecommerce/`.
    # Then I need to run docker-compose from `ecommerce/`.

    setup(file)

    path = Path(file)
    project_dir = path.parent.resolve()

    console.print(f"[dim]Switching context to {project_dir}[/dim]")
    os.chdir(project_dir)

    start(detach=True)

    console.print("[bold blue]Press Ctrl+C to stop logs...[/]")
    dm = DockerManager()
    dm.stream_logs()

if __name__ == "__main__":
    app()
