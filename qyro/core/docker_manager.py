import docker
import subprocess
import time
from rich.console import Console
from rich.prompt import Confirm

console = Console()

class DockerManager:
    def __init__(self):
        self.client = None

    def ensure_docker_running(self):
        """Checks if Docker daemon is running, if not prompts user."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            return True
        except (docker.errors.DockerException, Exception):
            console.print("[bold red]Error:[/] Docker is not running.")
            if Confirm.ask("Do you want me to try starting Docker (MacOS/Linux only)?"):
                return self._try_start_docker()
            else:
                console.print("[yellow]Please start Docker Desktop and try again.[/]")
                return False

    def _try_start_docker(self):
        # Very basic attempt for MacOS/Linux
        try:
            subprocess.run(["open", "-a", "Docker"], check=True) # MacOS
            console.print("[green]Attempting to start Docker... waiting 30s[/]")
            time.sleep(30)
            return self.ensure_docker_running()
        except:
            console.print("[red]Could not start Docker automatically.[/]")
            return False

    def run_compose(self, file: str = "docker-compose.yml", detach: bool = True):
        cmd = ["docker-compose", "-f", file, "up", "--build", "--remove-orphans"]
        if detach:
            cmd.append("-d")

        console.print(f"[bold blue]Running:[/bold blue] {' '.join(cmd)}")
        try:
            # We use subprocess because docker-py compose support is limited/complex
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Stream output
            for line in process.stdout:
                console.print(line.strip())
            for line in process.stderr:
                console.print(f"[dim]{line.strip()}[/dim]")

            process.wait()
            if process.returncode == 0:
                console.print("[bold green]Services started successfully![/]")
                return True
            else:
                console.print("[bold red]Failed to start services.[/]")
                return False
        except Exception as e:
            console.print(f"[bold red]Error running compose:[/] {e}")
            return False

    def stream_logs(self, file: str = "docker-compose.yml"):
        try:
            subprocess.run(["docker-compose", "-f", file, "logs", "-f"])
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping logs...[/]")
