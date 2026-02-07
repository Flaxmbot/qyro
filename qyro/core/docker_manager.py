import docker
import subprocess
import time
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    DownloadColumn,
)
from rich.table import Table
from rich.status import Status
from pathlib import Path
from qyro.core.templates import (
    DOCKERFILE_COMMON_BASE,
    DOCKERFILE_PYTHON_BASE,
    DOCKERFILE_NODE_BASE,
    DOCKERFILE_JAVA_BASE,
    DOCKERFILE_RUST_BASE,
    COMMON_BASE_IMAGE,
    PYTHON_BASE_IMAGE,
    NODE_BASE_IMAGE,
    JAVA_BASE_IMAGE,
    RUST_BASE_IMAGE
)

console = Console()

class DockerManager:
    def __init__(self):
        self.client = None
        self.max_retries = 3
        self.retry_delay = 5

    def ensure_docker_running(self):
        """Checks if Docker daemon is running, if not prompts user."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            console.print("[green]✓ Docker is running[/]")
            return True
        except (docker.errors.DockerException, Exception):
            console.print("[bold red]✗ Error: Docker is not running.[/]")
            if Confirm.ask("Do you want me to try starting Docker (MacOS/Linux only)?"):
                return self._try_start_docker()
            else:
                console.print("[yellow]Please start Docker Desktop and try again.[/]")
                return False

    def _try_start_docker(self):
        # Very basic attempt for MacOS/Linux
        try:
            subprocess.run(["open", "-a", "Docker"], check=True)  # MacOS
            with console.status("[green]Attempting to start Docker...[/]", spinner="dots"):
                time.sleep(30)
            return self.ensure_docker_running()
        except:
            console.print("[red]✗ Could not start Docker automatically.[/]")
            return False

    def pull_image_with_progress(self, image_name: str) -> bool:
        """Pull Docker image with progress tracking and retry logic."""
        for attempt in range(1, self.max_retries + 1):
            try:
                console.print(f"[blue]Pulling image: {image_name}[/] (Attempt {attempt}/{self.max_retries})")
                
                # Check if image already exists
                try:
                    self.client.images.get(image_name)
                    console.print(f"[green]✓ Image {image_name} already exists locally[/]")
                    return True
                except docker.errors.ImageNotFound:
                    pass
                
                # Pull with progress tracking
                with Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(bar_width=40),
                    TaskProgressColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                    TimeElapsedColumn(),
                    expand=True,
                ) as progress:
                    task = progress.add_task(f"Pulling {image_name}", total=None)
                    
                    # Use low-level API to get pull progress
                    stream = self.client.api.pull(
                        image_name,
                        stream=True,
                        decode=True
                    )
                    
                    last_status = None
                    for chunk in stream:
                        if "status" in chunk:
                            # Handle different status types
                            if chunk["status"] == "Pulling from":
                                progress.update(task, description=f"Pulling {chunk['from']}")
                            elif chunk["status"] == "Already exists":
                                pass
                            elif chunk["status"] == "Downloading":
                                if "progressDetail" in chunk and "total" in chunk["progressDetail"]:
                                    total = chunk["progressDetail"]["total"]
                                    current = chunk["progressDetail"]["current"]
                                    progress.update(
                                        task,
                                        total=total,
                                        completed=current,
                                        description=f"Downloading {chunk.get('id', image_name)}"
                                    )
                            elif chunk["status"] == "Extracting":
                                if "progressDetail" in chunk and "total" in chunk["progressDetail"]:
                                    total = chunk["progressDetail"]["total"]
                                    current = chunk["progressDetail"]["current"]
                                    progress.update(
                                        task,
                                        total=total,
                                        completed=current,
                                        description=f"Extracting {chunk.get('id', image_name)}"
                                    )
                            elif chunk["status"] == "Pull complete":
                                progress.update(task, description=f"[green]✓ Pull complete[/]")
                            else:
                                if chunk["status"] != last_status:
                                    progress.update(task, description=chunk["status"])
                                    last_status = chunk["status"]
                
                console.print(f"[green]✓ Image {image_name} pulled successfully[/]")
                return True
                
            except Exception as e:
                console.print(f"[red]✗ Error pulling {image_name}:[/] {e}")
                if attempt < self.max_retries:
                    console.print(f"[yellow]Retrying in {self.retry_delay} seconds...[/]")
                    time.sleep(self.retry_delay)
                else:
                    console.print(f"[bold red]✗ Failed to pull {image_name} after {self.max_retries} attempts[/]")
                    return False

    def build_base_images(self, adapter_path: Path):
        """Build language-specific base images with shared layers."""
        console.print("\n[bold blue]📦 Building language-specific base images...[/bold blue]")

        # Create a temporary build context for base images
        build_context = Path("qyro_build_context")
        build_context.mkdir(exist_ok=True)

        try:
            # Copy qyro adapters to build context
            adapters_dest = build_context / "qyro_adapters"
            if adapters_dest.exists():
                import shutil
                shutil.rmtree(adapters_dest)
            import shutil
            shutil.copytree(adapter_path, adapters_dest)

            # Build images with progress tracking
            images_to_build = [
                (COMMON_BASE_IMAGE, DOCKERFILE_COMMON_BASE),
                (PYTHON_BASE_IMAGE, DOCKERFILE_PYTHON_BASE),
                (NODE_BASE_IMAGE, DOCKERFILE_NODE_BASE),
                (JAVA_BASE_IMAGE, DOCKERFILE_JAVA_BASE),
                (RUST_BASE_IMAGE, DOCKERFILE_RUST_BASE),
            ]

            built_images = []
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                expand=True,
            ) as progress:
                total_task = progress.add_task(
                    "Total progress",
                    total=len(images_to_build)
                )
                
                for image_name, dockerfile_content in images_to_build:
                    task = progress.add_task(f"Checking {image_name}", total=None)
                    
                    try:
                        # Check if image already exists
                        try:
                            self.client.images.get(image_name)
                            console.print(f"\n[bold green]✓ Image {image_name} already exists locally[/bold green]")
                            built_images.append(image_name)
                            progress.advance(total_task)
                            continue
                        except docker.errors.ImageNotFound:
                            pass
                        
                        # Image not found, build it
                        console.print(f"\n[bold cyan]Building {image_name}[/bold cyan]")
                        
                        (build_context / "Dockerfile").write_text(dockerfile_content)
                        
                        # Build without streaming output for debugging
                        image, build_log = self.client.images.build(
                            path=str(build_context),
                            tag=image_name,
                            dockerfile="Dockerfile",
                            quiet=False
                        )
                        
                        # Print build log
                        for log in build_log:
                            if "stream" in log:
                                console.print(f"[dim]{log['stream'].strip()}[/dim]")
                        
                        built_images.append(image_name)
                        progress.advance(total_task)
                        
                    except Exception as e:
                        console.print(f"[bold red]✗ Error building {image_name}:[/] {e}")
                        return False

            # Show build summary
            console.print("\n[bold green]✓ All base images built successfully![/]")
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("Image Name", style="cyan")
            table.add_column("Status", style="green")
            for image in built_images:
                table.add_row(image, "✅ Built")
            console.print(table)
            
            return True
            
        except Exception as e:
            console.print(f"[bold red]✗ Error building base images:[/] {e}")
            return False
        finally:
            # Clean up build context
            import shutil
            shutil.rmtree(build_context)

    def run_compose(self, file: str = "docker-compose.yml", detach: bool = True):
        cmd = ["docker-compose", "-f", file, "up", "--build", "--remove-orphans"]
        if detach:
            cmd.append("-d")

        console.print(f"\n[bold blue]🚀 Starting services:[/bold blue] {' '.join(cmd)}")
        
        try:
            with Status("[green]Initializing Docker services...[/]", spinner="dots"):
                time.sleep(2)
                
            # We use subprocess because docker-py compose support is limited/complex
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Stream output with styling
            console.print("\n[bold blue]Service output:[/bold blue]")
            for line in process.stdout:
                line = line.strip()
                if line:
                    if "Pulling" in line or "Downloading" in line:
                        console.print(f"[cyan]{line}[/cyan]")
                    elif "Building" in line or "Step" in line:
                        console.print(f"[yellow]{line}[/yellow]")
                    elif "Successfully" in line or "done" in line.lower():
                        console.print(f"[green]✓ {line}[/green]")
                    elif "Error" in line or "Failed" in line:
                        console.print(f"[red]✗ {line}[/red]")
                    else:
                        console.print(line)
                        
            for line in process.stderr:
                line = line.strip()
                if line:
                    console.print(f"[dim red]⚠️ {line}[/dim red]")

            process.wait()
            if process.returncode == 0:
                console.print("\n[bold green]✅ Services started successfully![/]")
                return True
            else:
                console.print("\n[bold red]✗ Failed to start services.[/]")
                return False
                
        except Exception as e:
            console.print(f"\n[bold red]✗ Error running compose:[/] {e}")
            return False

    def stream_logs(self, file: str = "docker-compose.yml", service: str = None, follow: bool = True, tail: int = 100):
        try:
            cmd = ["docker-compose", "-f", file, "logs"]
            
            if follow:
                cmd.append("-f")
                
            cmd.extend(["--tail", str(tail)])
            
            if service:
                cmd.append(service)
                console.print(f"\n[bold blue]📋 Streaming logs for service {service}:[/bold blue]")
            else:
                console.print("\n[bold blue]📋 Streaming service logs:[/bold blue]")
                
            console.print("[dim]Press Ctrl+C to stop logging[/dim]\n")
            subprocess.run(cmd)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⏹️ Stopping logs...[/]")

    def check_images_availability(self, images: list) -> bool:
        """Check if required images are available and pull them if needed."""
        console.print("\n[bold blue]🔍 Checking image availability...[/bold blue]")
        
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Image", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Action", style="yellow")
        
        all_available = True
        
        for image in images:
            try:
                self.client.images.get(image)
                table.add_row(image, "[green]✅ Available[/]", "-")
            except docker.errors.ImageNotFound:
                table.add_row(image, "[red]❌ Missing[/]", "[yellow]Pulling[/yellow]")
                all_available = False
                
        console.print(table)
        
        if not all_available:
            console.print("\n[bold yellow]⚠️ Some images are missing. They will be pulled automatically.[/]")
            
        return all_available
