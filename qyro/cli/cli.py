"""
Qyro Command Line Interface
Provides commands for running, building, and managing Qyro applications.
"""

import sys
import os
import click
import asyncio
from pathlib import Path
from typing import Optional

# Import rich for beautiful output
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich import print as rprint
from rich.table import Table
from rich.tree import Tree
import pyfiglet

try:
    from qyro.orchestrator import QyroOrchestrator
    from qyro.common.kafka_manager import KafkaManager
    from qyro.common.config import QyroConfig
except ImportError:
    # Fallback for Docker container where qyro might not be in path
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    from qyro.orchestrator import QyroOrchestrator
    from qyro.common.kafka_manager import KafkaManager
    from qyro.common.config import QyroConfig

console = Console()

@click.group()
@click.version_option(version='2.0.0')
def main():
    """Qyro - Universal Polyglot Runtime"""
    # Display a beautiful banner using pyfiglet and rich
    ascii_banner = pyfiglet.figlet_format("QYRO", font="big")
    banner_text = Text(ascii_banner, style="bold cyan")
    
    panel = Panel(
        banner_text,
        title="[bold green]Universal Polyglot Runtime[/bold green]",
        subtitle="[italic white]Write Python, React, Rust, Java in one file with shared state[/italic white]",
        border_style="cyan",
        expand=False,
        padding=(1, 4)
    )
    console.print(panel)


@main.command()
@click.argument('qyro_file', type=click.Path(exists=True))
@click.option('--redis-host', default='localhost', help='Redis server hostname')
@click.option('--redis-port', default=6379, type=int, help='Redis server port')
@click.option('--redis-password', default=None, help='Redis password')
@click.option('--kafka-bootstrap-servers', default='localhost:9092', help='Kafka bootstrap servers')
@click.option('--skip-missing', is_flag=True, help='Skip missing dependencies during compilation')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def run(qyro_file: str, redis_host: str, redis_port: int, redis_password: Optional[str],
        kafka_bootstrap_servers: str, skip_missing: bool, debug: bool):
    """Run a Qyro application."""
    try:
        # Show startup info in a beautiful table
        table = Table(title="Runtime Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Parameter", style="dim", width=20)
        table.add_column("Value", min_width=20)

        table.add_row("Qyro File", qyro_file)
        table.add_row("Redis Host", redis_host)
        table.add_row("Redis Port", str(redis_port))
        table.add_row("Kafka Servers", kafka_bootstrap_servers)
        table.add_row("Debug Mode", str(debug))

        console.print(table)

        # Load configuration
        config = QyroConfig(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_password=redis_password,
            kafka_bootstrap_servers=kafka_bootstrap_servers,
            debug=debug
        )

        # Initialize Kafka manager (defer starting until async context)
        kafka_manager = KafkaManager(config)
        console.print("[green]Kafka Manager initialized (starting asynchronously)[/green]")

        # Create orchestrator with Kafka integration
        console.print("[bold green]Starting Qyro Orchestrator...[/bold green]")
        orchestrator = QyroOrchestrator(
            qyro_file=qyro_file,
            config=config,
            skip_missing=skip_missing
        )

        # Start the orchestrator
        console.print("\n[bold green]🚀 Qyro application is now running![/bold green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        orchestrator.start()

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        if 'orchestrator' in locals():
            orchestrator.shutdown()
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('qyro_file', type=click.Path(exists=True))
@click.option('--output-dir', default='./dist', help='Output directory for compiled artifacts')
@click.option('--target', default='docker', type=click.Choice(['docker', 'binary', 'kubernetes']),
              help='Target platform for deployment')
def build(qyro_file: str, output_dir: str, target: str):
    """Build a Qyro application for deployment."""
    from qyro.common.builder import QyroBuilder

    try:
        with console.status(f"[bold green]Building Qyro application for {target}...") as status:
            builder = QyroBuilder(qyro_file, output_dir, target)
            builder.build()
            console.log(f"Build completed successfully in {output_dir}")
        
        console.print(f"[bold green]✅ Build completed successfully in {output_dir}[/bold green]")
    except Exception as e:
        console.print(f"[red]Build failed: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8765, type=int, help='Port to listen on')
@click.option('--kafka-bootstrap-servers', default='localhost:9092', help='Kafka bootstrap servers')
def gateway(host: str, port: int, kafka_bootstrap_servers: str):
    """Start the Qyro gateway service."""
    try:
        from qyro.gateway import QyroGateway
    except ImportError:
        # Fallback for Docker container where qyro might not be in path
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from qyro.gateway import QyroGateway

    try:
        with console.status(f"[bold green]Starting Qyro Gateway on {host}:{port}...") as status:
            gateway = QyroGateway(
                host=host,
                port=port,
                kafka_bootstrap_servers=kafka_bootstrap_servers
            )
            console.log(f"Gateway started on {host}:{port}")
        gateway.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down gateway...[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Gateway error: {e}[/red]")
        sys.exit(1)


@main.command()
def version():
    """Show Qyro version."""
    console.print(f"[bold green]Qyro v2.0.0[/bold green]")


@main.command()
@click.argument('qyro_file', type=click.Path(exists=True))
@click.option('--build/--no-build', default=True, help='Build Docker images before running')
@click.option('--detached/--foreground', default=True, help='Run in detached mode (background)')
@click.option('--with-kafka/--without-kafka', default=False, help='Include Kafka in the setup')
def setup(qyro_file: str, build: bool, detached: bool, with_kafka: bool):
    """
    Automatically setup and run Qyro application in Docker.
    
    This command:
    1. Starts Redis (and optionally Kafka) in Docker containers
    2. Builds Docker images for your Qyro application
    3. Runs all services together using Docker Compose
    
    Requirements:
    - Docker and Docker Compose must be installed
    - Your qyro_file must be accessible from Docker
    
    Example:
        qyro setup my_app.qyro --with-kafka
    """
    import subprocess
    import tempfile
    import yaml
    import os
    from pathlib import Path

    # Check if Docker is available
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            console.print("[red]Error: Docker is not installed or not running.[/red]")
            return
        console.print(f"[green]Docker version: {result.stdout.strip()}[/green]")
    except FileNotFoundError:
        console.print("[red]Error: Docker is not installed or not in PATH.[/red]")
        return

    # Check if Docker Compose is available
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            # Try docker compose (newer versions)
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
            if result.returncode != 0:
                console.print("[red]Error: Docker Compose is not installed or not running.[/red]")
                return
        console.print("[green]Docker Compose is available[/green]")
    except FileNotFoundError:
        console.print("[red]Error: Docker Compose is not installed or not in PATH.[/red]")
        return

    # Determine the absolute path of the qyro file
    qyro_file_path = Path(qyro_file).resolve()
    qyro_file_name = qyro_file_path.name
    qyro_file_dir = qyro_file_path.parent
    
    # Get the Qyro project root (parent of qyro package)
    qyro_cli_dir = Path(__file__).resolve().parent.parent.parent
    
    # Create a temporary docker-compose file for this specific setup
    compose_config = {
        'version': '3.8',
        'services': {
            'redis': {
                'image': 'redis:7-alpine',
                'ports': ['6379:6379'],
                'volumes': ['redis-data:/data'],
                'networks': ['qyro-net'],
                'command': 'redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru',
                'healthcheck': {
                    'test': ['CMD', 'redis-cli', 'ping'],
                    'interval': '10s',
                    'timeout': '5s',
                    'retries': 5,
                    'start_period': '10s'
                },
                'restart': 'unless-stopped'
            }
        },
        'volumes': {
            'redis-data': {}
        },
        'networks': {
            'qyro-net': {
                'driver': 'bridge'
            }
        }
    }

    # Add Kafka if requested
    if with_kafka:
        compose_config['services']['zookeeper'] = {
            'image': 'confluentinc/cp-zookeeper:latest',
            'environment': {
                'ZOOKEEPER_CLIENT_PORT': '2181',
                'ZOOKEEPER_TICK_TIME': '2000'
            },
            'restart': 'unless-stopped'
        }

        compose_config['services']['kafka'] = {
            'image': 'confluentinc/cp-kafka:latest',
            'depends_on': ['zookeeper'],
            'ports': ['9092:9092'],
            'environment': {
                'KAFKA_BROKER_ID': '1',
                'KAFKA_ZOOKEEPER_CONNECT': 'zookeeper:2181',
                'KAFKA_ADVERTISED_LISTENERS': 'PLAINTEXT:host.docker.internal:9092',
                'KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR': '1'
            },
            'restart': 'unless-stopped'
        }

    # Add the orchestrator service
    compose_config['services']['orchestrator'] = {
        'build': {
            'context': str(qyro_cli_dir),
            'dockerfile': 'Dockerfile',
            'target': 'orchestrator'
        },
        'environment': [
            'REDIS_HOST=redis',
            'REDIS_PORT=6379',
            f'QYRO_FILE={qyro_file_name}',
            f'QYRO_FILE_DIR=/qyro_files'
        ],
        'depends_on': {
            'redis': {
                'condition': 'service_healthy'
            }
        },
        'volumes': [
            f'{str(qyro_file_dir)}:/qyro_files',
            '/dev/shm:/dev/shm'
        ],
        'networks': ['qyro-net'],
        'restart': 'unless-stopped'
    }

    # Add gateway service
    compose_config['services']['gateway'] = {
        'build': {
            'context': str(qyro_cli_dir),
            'dockerfile': 'Dockerfile',
            'target': 'gateway'
        },
        'ports': ['8000:8000', '8765:8765'],
        'environment': [
            'REDIS_HOST=redis',
            'REDIS_PORT=6379'
        ],
        'depends_on': {
            'redis': {
                'condition': 'service_healthy'
            }
        },
        'volumes': [
            f'{str(qyro_file_dir)}:/qyro_files'
        ],
        'networks': ['qyro-net'],
        'restart': 'unless-stopped',
        'healthcheck': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8000/health'],
            'interval': '30s',
            'timeout': '10s',
            'retries': 3,
            'start_period': '40s'
        }
    }

    # Create temporary docker-compose file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(compose_config, f)
        temp_compose_file = f.name

    try:
        # Build if requested
        if build:
            with console.status("[bold green]Building Docker images...") as status:
                build_cmd = ['docker-compose', '-f', temp_compose_file, 'build']
                result = subprocess.run(build_cmd)
                if result.returncode != 0:
                    console.print("[red]Error: Failed to build Docker images.[/red]")
                    return

        # Run the services
        with console.status("[bold green]Starting Qyro services...") as status:
            up_cmd = ['docker-compose', '-f', temp_compose_file]
            if detached:
                up_cmd.extend(['up', '-d'])
            else:
                up_cmd.extend(['up'])

            result = subprocess.run(up_cmd)
            if result.returncode != 0:
                console.print("[red]Error: Failed to start services.[/red]")
                return

        console.print(f"[bold green]🚀 Qyro application is now running![/bold green]")
        console.print(f"Gateway API available at: [blue]http://localhost:8000[/blue]")
        console.print(f"Gateway WebSocket available at: [blue]ws://localhost:8765/ws[/blue]")
        if with_kafka:
            console.print(f"Kafka broker running at: [blue]localhost:9092[/blue]")
        console.print(f"Redis server running at: [blue]localhost:6379[/blue]")

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_compose_file)
        except:
            pass


@main.command()
def init():
    """Initialize a new Qyro project."""
    from .interactive import init_project
    init_project()


if __name__ == '__main__':
    main()
