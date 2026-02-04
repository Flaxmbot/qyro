import sys
import os
import time
import threading
import argparse
import colorama
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.spinner import Spinner
import pyfiglet
from art import tprint

# Add qyro to the Python path to ensure modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qyro'))

try:
    from qyro.orchestrator.orchestrator import QyroOrchestrator
    from qyro.common.config import QyroConfig
    from qyro.common.redis_memory import RedisConnectionError
    from qyro.gateway.gateway import QyroGateway
except ImportError:
    # Fallback for Docker container where qyro might not be in path
    from qyro.orchestrator.orchestrator import QyroOrchestrator
    from qyro.common.config import QyroConfig
    from qyro.common.redis_memory import RedisConnectionError
    from qyro.gateway.gateway import QyroGateway

# Initialize colorama for cross-platform color support
colorama.init()
console = Console()

def animate_text(text, delay=0.05):
    """Animate text character by character."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()  # newline at the end

def show_loading_animation(stop_event, message="Loading"):
    """Show a loading animation."""
    chars = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        print(f"\r{message} {chars[idx % len(chars)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    print("\r", end="", flush=True)  # Clear the line

def show_rich_loading(message="Processing"):
    """Show a rich loading animation."""
    spinner = Spinner("dots", style="green")
    text = Text(message, style="bold blue")
    panel = Panel(spinner, title=text, border_style="blue")

    with Live(panel, refresh_per_second=20):
        # Wait for the stop_event
        while not hasattr(show_rich_loading, '_stop_flag') or not show_rich_loading._stop_flag:
            time.sleep(0.1)

    # Reset the flag after stopping
    show_rich_loading._stop_flag = False

def print_colored(text, color=colorama.Fore.WHITE):
    """Print text in color."""
    print(f"{color}{text}{colorama.Style.RESET_ALL}")

def print_header():
    """Print the Qyro header with animated ASCII art."""
    # Create animated ASCII art using pyfiglet
    ascii_art = pyfiglet.figlet_format("QYRO", font="slant")

    # Display with rich for enhanced formatting
    header_text = Text(ascii_art, style="bold cyan")
    subtitle = Text("\nPolyglot Runtime v2.0 - NBP v3 Protocol", style="bold magenta")

    # Animate the header
    console.print(header_text, end="")
    time.sleep(0.2)
    console.print(subtitle)

    # Add a decorative line
    console.print(Panel("", title="[bold green]Initializing Qyro Runtime[/bold green]", expand=False))

def check_redis_availability(host, port, db, password):
    """
    Check if Redis is available before starting the orchestrator.

    Args:
        host: Redis server hostname
        port: Redis server port
        db: Redis database number
        password: Redis password (optional)

    Returns:
        bool: True if Redis is available, False otherwise
    """
    try:
        import redis
        from redis.exceptions import ConnectionError as RedisConnectionError

        print_colored(f"[QYRO] Checking Redis availability at {host}:{port}...", colorama.Fore.CYAN)

        # Create a test connection
        redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            decode_responses=True
        )

        # Test connection with ping
        redis_client.ping()

        print_colored(f"[QYRO] Redis connection successful!", colorama.Fore.GREEN)
        return True

    except ImportError:
        print_colored("[QYRO] Redis library not installed. Install with: pip install redis>=5.0.0", colorama.Fore.YELLOW)
        return False
    except RedisConnectionError as e:
        print_colored(f"[QYRO] Redis connection failed: {e}", colorama.Fore.YELLOW)
        return False
    except Exception as e:
        print_colored(f"[QYRO] Redis check error: {e}", colorama.Fore.YELLOW)
        return False

def check_kafka_availability(bootstrap_servers):
    """
    Check if Kafka is available before starting the orchestrator.

    Args:
        bootstrap_servers: Kafka bootstrap servers

    Returns:
        bool: True if Kafka is available, False otherwise
    """
    try:
        from confluent_kafka.admin import AdminClient

        print_colored(f"[QYRO] Checking Kafka availability at {bootstrap_servers}...", colorama.Fore.CYAN)

        # Create a test admin client
        conf = {'bootstrap.servers': bootstrap_servers}
        admin_client = AdminClient(conf)

        # Test connection by listing topics
        metadata = admin_client.list_topics(timeout=5)

        print_colored(f"[QYRO] Kafka connection successful! Found {len(metadata.topics)} topics.", colorama.Fore.GREEN)
        return True

    except ImportError:
        print_colored("[QYRO] Kafka library not installed. Install with: pip install confluent-kafka>=2.0.0", colorama.Fore.YELLOW)
        return False
    except Exception as e:
        print_colored(f"[QYRO] Kafka check error: {e}", colorama.Fore.YELLOW)
        return False

def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Qyro Polyglot Runtime - Run Qyro applications with Kafka and Redis-based inter-process communication',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py main.qyro
  python run.py main.qyro --redis-host localhost --redis-port 6379 --kafka-bootstrap-servers localhost:9092
  python run.py main.qyro --redis-host redis.example.com --redis-password secret --kafka-bootstrap-servers kafka.example.com:9092
        """
    )

    # Positional argument for the qyro file
    parser.add_argument(
        'qyro_file',
        help='Path to the main.qyro file to run'
    )

    # Redis connection arguments
    redis_group = parser.add_argument_group('Redis Connection Options')
    redis_group.add_argument(
        '--redis-host',
        default='localhost',
        help='Redis server hostname (default: localhost)'
    )
    redis_group.add_argument(
        '--redis-port',
        type=int,
        default=6379,
        help='Redis server port (default: 6379)'
    )
    redis_group.add_argument(
        '--redis-db',
        type=int,
        default=0,
        help='Redis database number (default: 0)'
    )
    redis_group.add_argument(
        '--redis-password',
        default=None,
        help='Redis password (optional)'
    )

    # Kafka connection arguments
    kafka_group = parser.add_argument_group('Kafka Connection Options')
    kafka_group.add_argument(
        '--kafka-bootstrap-servers',
        default='localhost:9092',
        help='Kafka bootstrap servers (default: localhost:9092)'
    )

    # Additional options
    parser.add_argument(
        '--skip-missing',
        action='store_true',
        help='Skip missing dependencies during compilation'
    )

    return parser.parse_args()

def main():
    """Main entry point for the Qyro runtime."""
    # Parse command-line arguments
    args = parse_arguments()

    # Check if Docker is available and if user wants to run in Docker
    import subprocess
    import os
    use_docker = os.environ.get('QYRO_USE_DOCKER', '').lower() in ('true', '1', 'yes')

    if not use_docker:
        # Ask user if they want to run in Docker if Docker is available
        try:
            docker_result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            compose_result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if docker_result.returncode == 0 and (compose_result.returncode == 0 or
                                                  subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True).returncode == 0):
                response = input("Docker is available. Would you like to run this application in Docker? (y/N): ")
                if response.lower() in ('y', 'yes'):
                    # Use the CLI setup command to run in Docker
                    import sys
                    setup_cmd = [sys.executable, '-m', 'qyro.cli.cli', 'setup', args.qyro_file]
                    if not check_redis_availability(args.redis_host, args.redis_port, args.redis_db, args.redis_password):
                        setup_cmd.append('--with-kafka')  # Use Kafka if Redis isn't available
                    subprocess.run(setup_cmd)
                    return
        except (FileNotFoundError, subprocess.SubprocessError):
            # Docker not available, continue with local execution
            pass

    # Force UTF-8 for stdout/stderr on Windows to avoid charmap errors
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # Print animated header
    print_header()

    # Show startup animation with rich
    startup_spinner = Spinner("clock", style="cyan")
    startup_text = Text("Initializing The Singularity", style="bold yellow")
    startup_panel = Panel(startup_spinner, title=startup_text, border_style="yellow")

    with Live(startup_panel, refresh_per_second=20) as live:
        # Simulate some startup delay for animation effect
        time.sleep(1.5)

        orchestrator = None
        redis_available = False
        kafka_available = False

        try:
            # Check Redis availability
            redis_available = check_redis_availability(
                host=args.redis_host,
                port=args.redis_port,
                db=args.redis_db,
                password=args.redis_password
            )

            # Check Kafka availability
            kafka_available = check_kafka_availability(args.kafka_bootstrap_servers)

            if not redis_available:
                console.print("[QYRO] WARNING: Redis is not available. Running in degraded mode.", style="yellow")
                console.print("[QYRO] Some features will be unavailable (shared state, pub/sub, etc.).", style="yellow")
            else:
                console.print(f"[QYRO] Redis-based runtime enabled at {args.redis_host}:{args.redis_port}", style="green")

            if not kafka_available:
                console.print("[QYRO] WARNING: Kafka is not available. Running in degraded mode.", style="yellow")
                console.print("[QYRO] Some features will be unavailable (reliable messaging, event streaming, etc.).", style="yellow")
            else:
                console.print(f"[QYRO] Kafka-based messaging enabled at {args.kafka_bootstrap_servers}", style="green")

            console.print("[QYRO] Singularity Active!", style="bold green")

            # Create configuration
            config = QyroConfig(
                redis_host=args.redis_host,
                redis_port=args.redis_port,
                redis_db=args.redis_db,
                redis_password=args.redis_password,
                kafka_bootstrap_services=args.kafka_bootstrap_servers
            )

            # Create orchestrator with configuration
            orchestrator = QyroOrchestrator(
                qyro_file=args.qyro_file,
                config=config,
                skip_missing=args.skip_missing
            )

            # Log orchestrator initialization
            if redis_available and kafka_available:
                console.print(f"[QYRO] Orchestrator initialized with Redis and Kafka connections", style="green")
            elif redis_available:
                console.print(f"[QYRO] Orchestrator initialized with Redis connection (Kafka unavailable)", style="yellow")
            elif kafka_available:
                console.print(f"[QYRO] Orchestrator initialized with Kafka connection (Redis unavailable)", style="yellow")
            else:
                console.print(f"[QYRO] Orchestrator initialized (Redis and Kafka unavailable)", style="red")


            # Start Gateway Service
            console.print("[QYRO] Starting Gateway Service...", style="cyan")

            # Show gateway loading animation
            gateway_spinner = Spinner("clock", style="cyan")
            gateway_text = Text("Starting Gateway Service", style="bold cyan")
            gateway_panel = Panel(gateway_spinner, title=gateway_text, border_style="cyan")

            with Live(gateway_panel, refresh_per_second=20) as gateway_live:
                gateway = QyroGateway(
                    host="0.0.0.0",
                    port=8765,
                    kafka_bootstrap_servers=args.kafka_bootstrap_servers
                )

                # Run gateway in a separate thread
                def run_gateway():
                    gateway.start()

                gateway_thread = threading.Thread(target=run_gateway, daemon=True)
                gateway_thread.start()

                # Simulate gateway startup delay
                time.sleep(1)

                console.print("[QYRO] Gateway active at http://localhost:8765", style="green")

            # Start the orchestrator with animation
            console.print("[QYRO] Starting Orchestrator...", style="cyan")
            orchestrator_spinner = Spinner("clock", style="green")
            orchestrator_text = Text("Starting Orchestrator", style="bold green")
            orchestrator_panel = Panel(orchestrator_spinner, title=orchestrator_text, border_style="green")

            with Live(orchestrator_panel, refresh_per_second=20) as orchestrator_live:
                time.sleep(1)  # Simulate startup delay
                orchestrator.start()

        except KeyboardInterrupt:
            console.print("\n[QYRO] Shutdown initiated by user...", style="red")

            # Graceful shutdown
            if orchestrator:
                orchestrator.shutdown()

            sys.exit(0)
        except RedisConnectionError as e:
            console.print(f"\n[QYRO] Redis connection error: {e}", style="red")
            console.print("[QYRO] Continuing without Redis - some features will be unavailable.", style="yellow")

            # Create configuration without Redis
            config = QyroConfig(
                kafka_bootstrap_servers=args.kafka_bootstrap_servers
            )

            # Try to start orchestrator without Redis
            try:
                orchestrator = QyroOrchestrator(
                    qyro_file=args.qyro_file,
                    config=config,
                    skip_missing=args.skip_missing
                )

                # Show orchestrator loading animation
                orchestrator_spinner = Spinner("clock", style="green")
                orchestrator_text = Text("Starting Orchestrator", style="bold green")
                orchestrator_panel = Panel(orchestrator_spinner, title=orchestrator_text, border_style="green")

                with Live(orchestrator_panel, refresh_per_second=20) as orchestrator_live:
                    time.sleep(1)  # Simulate startup delay
                    orchestrator.start()

            except Exception as inner_e:
                console.print(f"\n[QYRO] Fatal error: {inner_e}", style="red")
                import traceback
                traceback.print_exc()
                sys.exit(1)

        except Exception as e:
            console.print(f"\n[QYRO] Fatal error: {e}", style="red")
            import traceback
            traceback.print_exc()

            # Attempt graceful shutdown if orchestrator was created
            if orchestrator:
                try:
                    orchestrator.shutdown()
                except Exception as shutdown_error:
                    console.print(f"[QYRO] Error during shutdown: {shutdown_error}", style="red")

            sys.exit(1)

if __name__ == "__main__":
    main()
