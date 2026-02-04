"""
Nexus Process Orchestrator with Kafka Integration
Manages lifecycle of polyglot processes with improved supervision,
Kafka-based messaging, and graceful error handling.
"""

import os
import sys
import time
import threading
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

import colorama
from colorama import Fore, Style

from qyro.common.parser import QyroParser
from qyro.common.compiler import QyroCompiler
from qyro.common.schema_loader import QyroSchemaLoader
from qyro.common.logging import get_logger
from qyro.common.platform import get_platform
from qyro.common.kafka_manager import KafkaManager
from qyro.common.config import QyroConfig
from qyro.common.redis_memory import RedisQyroMemory, RedisConnectionError
from qyro.common.secure_sandbox import get_secure_sandbox
from qyro.common.monitoring import get_monitor

# colorama.init() - Disabled to prevent interference with UTF-8 stdout wrapper
if sys.platform == 'win32':
    try:
        from colorama import just_fix_windows_console
        just_fix_windows_console()
    except ImportError:
        # Fallback for older colorama
        colorama.init(strip=False, convert=False)
else:
    colorama.init()
logger = get_logger("nexus.orchestrator")
monitor = get_monitor()


@dataclass
class ProcessInfo:
    """Information about a supervised process."""
    artifact: Dict[str, Any]
    name: str
    cmd: List[str]
    proc: Optional[subprocess.Popen] = None
    restarts: int = 0
    last_crash: float = 0.0
    backoff_seconds: float = 1.0
    status: str = "unknown"  # running, crashed, stopped, backoff


class ProcessSupervisor:
    """Handles process supervision and lifecycle management."""

    def __init__(self, max_restarts: int = 10, initial_backoff: float = 1.0, max_backoff: float = 60.0):
        self.max_restarts = max_restarts
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff

    def handle_process_crash(self, p_info: ProcessInfo, return_code: int) -> bool:
        """Handle a process crash and determine if it should be restarted."""
        now = time.time()
        p_info.last_crash = now

        logger.warning("process_crashed", name=p_info.name, code=return_code, restarts=p_info.restarts)

        # Check restart limit
        if p_info.restarts >= self.max_restarts:
            logger.error(f"Process {p_info.name} exceeded max restarts ({self.max_restarts}). Giving up.")
            p_info.status = "failed"
            return False

        # Enter backoff
        p_info.status = "backoff"
        p_info.restarts += 1
        p_info.backoff_seconds = min(p_info.backoff_seconds * 2, self.max_backoff)

        logger.info(f"Waiting {p_info.backoff_seconds:.1f}s before restart (attempt {p_info.restarts}/{self.max_restarts})...")
        return True

    def should_restart_process(self, p_info: ProcessInfo) -> bool:
        """Check if a process should be restarted based on backoff period."""
        now = time.time()
        return now - p_info.last_crash >= p_info.backoff_seconds


class QyroOrchestrator:
    """
    Orchestrates the lifecycle of multiple polyglot processes with Kafka integration.

    Features:
    - Process supervision with crash detection
    - Exponential backoff for restarts (prevents crash loops)
    - Maximum restart limit per process
    - Kafka-based inter-module communication
    - Redis-based shared state
    - Graceful shutdown with timeout
    - Health monitoring
    """

    def __init__(
        self,
        qyro_file: str,
        config: QyroConfig,
        skip_missing: bool = True,
    ):
        self.qyro_file = qyro_file
        self.config = config
        self.parser = QyroParser()()
        self.compiler = QyroCompiler(skip_missing=skip_missing)
        self.schema_loader = QyroSchemaLoader()()
        self.platform = get_platform()
        self.running = True
        self.processes: List[ProcessInfo] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self.skip_missing = skip_missing
        self.supervisor = ProcessSupervisor(
            max_restarts=config.max_restarts,
            initial_backoff=config.restart_backoff
        )

        # Kafka manager for messaging
        self.kafka_manager: Optional[KafkaManager] = None
        
        # Redis memory instance (initialized in start())
        self.memory: Optional[RedisQyroMemory] = None
        self._redis_available = False
        self._use_distributed_memory = False

        # Output monitoring thread
        self._output_monitor_thread: Optional[threading.Thread] = None

    def start(self):
        """Start the orchestrator with Kafka and Redis integration."""
        self._print_banner()

        try:
            logger.info(f"Parsing {self.QYRO_file}...")
            self.parser.parse_file(self.QYRO_file)

            # Initialize Kafka manager
            self._initialize_kafka_manager()

            # Initialize Redis memory
            self._initialize_redis_memory()

            if self.parser.blocks.get('schema'):
                logger.info("Detecting Schema...")
                try:
                    initial_state = self.schema_loader.process_schema(self.parser.blocks['schema'][0])
                    
                    # Initialize schema state in Redis
                    if initial_state and self._redis_available:
                        self.memory.write(initial_state)
                        logger.info(f"Schema initialized in Redis (Size: {len(str(initial_state))})")
                        
                        # Also publish initial state to Kafka
                        if self.kafka_manager:
                            import asyncio
                            asyncio.create_task(
                                self.kafka_manager.publish_state_change(initial_state, 'orchestrator')
                            )
                    elif initial_state:
                        logger.info(f"Schema detected (Size: {len(str(initial_state))})")
                        logger.warning("Redis not available, schema not persisted.")
                except Exception as e:
                    logger.error(f"SCHEMA INIT ERROR: {e}")
                    raise e
            else:
                logger.info("No schema block found.")

            # Cleanup stale binaries BEFORE compilation to avoid permission errors on Windows
            self._cleanup_stale_processes()

            logger.info("Compiling modules...")
            artifacts = self.compiler.compile(self.parser.blocks)

            # Check for frontend blocks and prepare them
            frontend_types = [a['type'] for a in artifacts if a['type'] in ['react', 'nextjs']]
            if frontend_types:
                self._prepare_frontend(frontend_types[0])

            self._spawn_processes(artifacts)

            # Start the centralized output monitoring thread
            self._output_monitor_thread = threading.Thread(target=self._monitor_all_outputs, daemon=True)
            self._output_monitor_thread.start()

            # Subscribe to Kafka state changes to update Redis
            if self.kafka_manager:
                import asyncio
                asyncio.create_task(self._subscribe_to_kafka_state_changes())

            self._main_loop()

        except KeyboardInterrupt:
            logger.info("keyboard_interrupt")
            self.shutdown()
        except Exception as e:
            logger.error("orchestrator_error", error=str(e))
            self.antigravity_protocol(e)

    def _initialize_kafka_manager(self):
        """Initialize Kafka manager for messaging."""
        try:
            print(f"{Fore.CYAN}[QYRO] Initializing Kafka at {self.config.kafka_bootstrap_servers}...{Style.RESET_ALL}")
            self.kafka_manager = KafkaManager(self.config)
            
            # Start Kafka manager
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.kafka_manager.start_producer())
            
            logger.info("kafka_manager_initialized", servers=self.config.kafka_bootstrap_servers)
        except Exception as e:
            logger.warning("kafka_init_error", error=str(e))
            logger.warning("Continuing without Kafka - some features will be unavailable.")
            self.kafka_manager = None

    def _initialize_redis_memory(self):
        """Initialize Redis memory and set up event subscriptions."""
        try:
            print(f"{Fore.CYAN}[QYRO] Connecting to Redis at {self.config.redis_host}:{self.config.redis_port}...{Style.RESET_ALL}")
            self.memory = RedisQyroMemory(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password
            )
            self._redis_available = True

            # Register the orchestrator as a module
            self.memory.register_module(
                'orchestrator',
                {
                    'version': '2.0',
                    'language': 'python',
                    'pid': os.getpid(),
                    'metadata': {
                        'type': 'orchestrator',
                        'QYRO_file': self.QYRO_file
                    }
                }
            )

            # Subscribe to state changes
            self.memory.subscribe_to_changes(self._on_state_change)

            # Subscribe to events
            self.memory.subscribe_to_events(self._on_redis_event)

            # Subscribe to broadcasts
            self.memory.subscribe_to_broadcasts(self._on_broadcast)

            logger.info("redis_memory_initialized", host=self.config.redis_host, port=self.config.redis_port)

        except RedisConnectionError as e:
            logger.warning("redis_connection_failed", error=str(e))
            logger.warning("Continuing without Redis - some features will be unavailable.")
            self._redis_available = False
        except Exception as e:
            logger.warning("redis_init_error", error=str(e))
            logger.warning("Continuing without Redis - some features will be unavailable.")
            self._redis_available = False

    async def _subscribe_to_kafka_state_changes(self):
        """Subscribe to Kafka state changes and update Redis."""
        if not self.kafka_manager:
            return
            
        async def state_change_handler(state_diff):
            if self._redis_available and self.memory:
                try:
                    self.memory.update_fields(state_diff)
                    logger.debug("state_updated_from_kafka", keys=list(state_diff.keys()))
                except Exception as e:
                    logger.error("redis_update_from_kafka_failed", error=str(e))
        
        await self.kafka_manager.subscribe_to_state_changes(state_change_handler)

    def _on_state_change(self, state: Dict[str, Any]):
        """Handle state change events from Redis."""
        logger.debug("state_change_received", keys=list(state.keys()))

    def _on_redis_event(self, event):
        """Handle general events from Redis."""
        logger.debug("redis_event_received", event_type=event.event_type, source=event.source)

        # Handle module registration events
        if event.event_type == 'module_registered':
            module_name = event.data.get('name')
            if module_name:
                logger.info(f"Module registered: {module_name}")

        # Handle module unregistration events
        elif event.event_type == 'module_unregistered':
            module_name = event.data.get('module')
            if module_name:
                logger.warning(f"Module unregistered: {module_name}")

        # Handle module state change events
        elif event.event_type == 'module_state_changed':
            module_name = event.data.get('module')
            if module_name:
                logger.debug("module_state_changed", module=module_name)

    def _on_broadcast(self, message: Dict[str, Any]):
        """Handle broadcast messages from Redis."""
        logger.debug("broadcast_received", message=message)

    def _stream_output(self, pipe, name, is_stderr=False):
        """Stream output from a pipe to stdout."""
        try:
            for line in iter(pipe.readline, ''):
                if not line:
                    break
                # Remove trailing newline
                line = line.rstrip()
                if not line:
                    continue

                # Colorize output based on source
                prefix_color = Fore.RED if is_stderr else Fore.CYAN
                # Check for "Link:" or http/https URLs to highlight
                if "Link:" in line or "http://" in line or "https://" in line:
                    # Highlight URL if present
                    if "http" in line:
                        import re
                        url_pattern = r'(https?://[^\s]+)'
                        line = re.sub(url_pattern, f"{Fore.YELLOW}{Style.BRIGHT}\\1{Style.RESET_ALL}{prefix_color}", line)

                    self._safe_print(f"{prefix_color}[{name}] {line}{Style.RESET_ALL}")
                    self._safe_print(f"{Fore.GREEN}{Style.BRIGHT}>>> ACCESS LINK ABOVE <<<{Style.RESET_ALL}")
                else:
                    self._safe_print(f"{prefix_color}[{name}] {line}{Style.RESET_ALL}")

        except ValueError:
            pass  # Pipe closed
        except Exception as e:
            # Only log real errors, not pipe closures during shutdown
            if self.running:
                logger.error("stream_error", name=name, error=str(e))

    def _monitor_all_outputs(self):
        """Monitor output from all processes using a single thread with select() for efficiency."""
        import select
        import io

        # Collect all pipes to monitor
        all_pipes = []
        pipe_info = {}  # Maps pipe object to (name, is_stderr) tuple

        for p_info in self.processes:
            if p_info.proc:
                if p_info.proc.stdout:
                    all_pipes.append(p_info.proc.stdout)
                    pipe_info[p_info.proc.stdout] = (p_info.name, False)
                if p_info.proc.stderr:
                    all_pipes.append(p_info.proc.stderr)
                    pipe_info[p_info.proc.stderr] = (p_info.name, True)

        # Use select to efficiently wait for data on any pipe (Unix-like systems)
        # For Windows, we'll use a different approach
        if sys.platform == 'win32':
            # On Windows, use a simpler approach with a single queue and threads per pipe
            import queue
            import threading

            output_queue = queue.Queue()

            def pipe_reader(pipe, name, is_stderr):
                """Read from a single pipe and put output in shared queue."""
                try:
                    while self.running:
                        line = pipe.readline()
                        if not line:
                            break
                        output_queue.put((name, is_stderr, line.rstrip()))
                except Exception:
                    pass  # Pipe closed or other error

            # Start a thread for each pipe
            reader_threads = []
            for p_info in self.processes:
                if p_info.proc:
                    if p_info.proc.stdout:
                        t = threading.Thread(
                            target=pipe_reader,
                            args=(p_info.proc.stdout, p_info.name, False),
                            daemon=True
                        )
                        t.start()
                        reader_threads.append(t)

                    if p_info.proc.stderr:
                        t = threading.Thread(
                            target=pipe_reader,
                            args=(p_info.proc.stderr, p_info.name, True),
                            daemon=True
                        )
                        t.start()
                        reader_threads.append(t)

            # Process output from the shared queue
            while self.running:
                try:
                    try:
                        name, is_stderr, line = output_queue.get(timeout=0.01)
                        if line:
                            # Colorize output based on source
                            prefix_color = Fore.RED if is_stderr else Fore.CYAN
                            # Check for "Link:" or http/https URLs to highlight
                            if "Link:" in line or "http://" in line or "https://" in line:
                                if "http" in line:
                                    import re
                                    url_pattern = r'(https?://[^\s]+)'
                                    line = re.sub(url_pattern, f"{Fore.YELLOW}{Style.BRIGHT}\\1{Style.RESET_ALL}{prefix_color}", line)

                                self._safe_print(f"{prefix_color}[{name}] {line}{Style.RESET_ALL}")
                                self._safe_print(f"{Fore.GREEN}{Style.BRIGHT}>>> ACCESS LINK ABOVE <<<{Style.RESET_ALL}")
                            else:
                                self._safe_print(f"{prefix_color}[{name}] {line}{Style.RESET_ALL}")
                    except queue.Empty:
                        continue
                except Exception:
                    time.sleep(0.01)
        else:
            # Unix-like systems: use select for efficient I/O multiplexing
            while self.running:
                try:
                    # Use select to wait for data on any of the pipes
                    ready_pipes, _, _ = select.select(all_pipes, [], [], 0.1)

                    for pipe in ready_pipes:
                        try:
                            line = pipe.readline()
                            if line:
                                name, is_stderr = pipe_info[pipe]
                                line = line.rstrip()

                                if line:
                                    # Colorize output based on source
                                    prefix_color = Fore.RED if is_stderr else Fore.CYAN
                                    # Check for "Link:" or http/https URLs to highlight
                                    if "Link:" in line or "http://" in line or "https://" in line:
                                        if "http" in line:
                                            import re
                                            url_pattern = r'(https?://[^\s]+)'
                                            line = re.sub(url_pattern, f"{Fore.YELLOW}{Style.BRIGHT}\\1{Style.RESET_ALL}{prefix_color}", line)

                                        self._safe_print(f"{prefix_color}[{name}] {line}{Style.RESET_ALL}")
                                        self._safe_print(f"{Fore.GREEN}{Style.BRIGHT}>>> ACCESS LINK ABOVE <<<{Style.RESET_ALL}")
                                    else:
                                        self._safe_print(f"{prefix_color}[{name}] {line}{Style.RESET_ALL}")
                            else:
                                # EOF reached, remove pipe from monitoring
                                if pipe in all_pipes:
                                    all_pipes.remove(pipe)
                        except Exception:
                            # If we can't read from the pipe, remove it
                            if pipe in all_pipes:
                                all_pipes.remove(pipe)

                except Exception as e:
                    # Brief pause to avoid tight loop if there are issues
                    time.sleep(0.01)

    def _launch_process(self, art: Dict[str, Any], existing: Optional[ProcessInfo] = None) -> Optional[ProcessInfo]:
        """Launch a single process from an artifact with platform abstraction."""
        try:
            cmd = []
            name = "Unknown"
            launch_cwd = None

            if art['type'] == 'c':
                name = art['bin']
                cmd = [f"./{art['bin']}"]
            elif art['type'] == 'rs':
                name = art['bin']
                cmd = [f"./{art['bin']}"]
            elif art['type'] == 'java':
                # Java modules now use NexusModuleRunner wrapper
                # The wrapper expects the user class name as an argument
                user_class = art.get('user_class', art['class'])
                name = f"{art['class']}({user_class})"
                cp = art.get('cp', '.')

                # Add JAR files from lib directory to classpath if they exist
                lib_dir = "lib"
                classpath_sep = ';' if self.platform.is_windows() else ':'

                if os.path.exists(lib_dir):
                    for jar_file in os.listdir(lib_dir):
                        if jar_file.endswith('.jar'):
                            cp += f"{classpath_sep}{lib_dir}/{jar_file}"

                cmd = ["java", "-cp", cp, art['class'], user_class]
            elif art['type'] == 'go':
                name = art['bin']
                cmd = [f"./{art['bin']}"]
            elif art['type'] == 'ts':
                name = art['src']
                cmd = ["npx", "ts-node", art['src']]
            elif art['type'] == 'web':
                name = art['src']
                cmd = ["uvicorn", art['src'].replace('.py', ':app'), "--reload", "--port", "8000"]
            elif art['type'] == 'py':
                name = art['src']
                cmd = ["python", "-u", art['src']]  # -u for unbuffered output
            elif art['type'] == 'react':
                name = "React-Frontend"
                # Frontend is in QYRO_frontend/
                cmd = ["npm", "start"]
                launch_cwd = "QYRO_frontend"
                # Check for package.json to ensure it's ready
                if not os.path.exists(os.path.join(launch_cwd, "package.json")):
                    logger.warning(f"React Frontend not initialized. Skipping launch.")
                    return None
            elif art['type'] == 'nextjs':
                name = "NextJS-Frontend"
                cmd = ["npm", "run", "dev"]
                launch_cwd = "QYRO_frontend"
                if not os.path.exists(os.path.join(launch_cwd, "package.json")):
                    logger.warning("Next.js Frontend not initialized. Skipping launch.")
                    return None

            if not cmd:
                logger.warning("unknown_artifact_type", artifact=art)
                return None

            # Windows Robustness: Kill any existing process with the same name to avoid 'Permission Denied'
            # (Already handled in _cleanup_stale_processes, but good for dynamic restarts)
            if self.platform.is_windows() and art['type'] in ['c', 'rs', 'go']:
                try:
                    self.platform.kill_process_by_name(name, force=True)
                except:
                    pass

            logger.info(f"Launching {art['type'].upper()} Module: {name}")

            # Use shell=True only for TypeScript (npx issues on Windows)
            use_shell = art['type'] in ['ts', 'react', 'nextjs']

            # Prepare environment with Redis and Kafka connection info
            env = os.environ.copy()
            if self._redis_available:
                env['QYRO_REDIS_HOST'] = self.config.redis_host
                env['QYRO_REDIS_PORT'] = str(self.config.redis_port)
                env['QYRO_REDIS_DB'] = str(self.config.redis_db)
                if self.config.redis_password:
                    env['QYRO_REDIS_PASSWORD'] = self.config.redis_password
                env['QYRO_MODULE_NAME'] = name
                
            # Add Kafka configuration to environment
            if self.kafka_manager:
                env['QYRO_KAFKA_BOOTSTRAP_SERVERS'] = self.config.kafka_bootstrap_servers
                env['QYRO_KAFKA_TOPIC_PREFIX'] = self.config.kafka_topic_prefix
                env['QYRO_MODULE_NAME'] = name

            # SECURITY: Apply resource limits to prevent runaway processes
            def apply_resource_limits():
                """Apply resource limits in child process."""
                import resource
                try:
                    # Limit virtual memory to max_memory_mb (in bytes)
                    if hasattr(resource, 'RLIMIT_AS'):
                        max_memory = self.config.max_memory_mb * 1024 * 1024  # Convert MB to bytes
                        resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))

                    # Limit CPU time based on configuration
                    if hasattr(resource, 'RLIMIT_CPU'):
                        max_cpu_time = 300  # 5 minutes - configurable
                        resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_time, max_cpu_time))

                    # Limit number of file descriptors to prevent resource exhaustion
                    if hasattr(resource, 'RLIMIT_NOFILE'):
                        max_fds = 32  # Conservative limit for most applications
                        resource.setrlimit(resource.RLIMIT_NOFILE, (max_fds, max_fds))

                    # Limit core file size to prevent disk exhaustion
                    if hasattr(resource, 'RLIMIT_CORE'):
                        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

                    # Limit stack size to prevent stack overflow
                    if hasattr(resource, 'RLIMIT_STACK'):
                        max_stack = 8 * 1024 * 1024  # 8 MB
                        resource.setrlimit(resource.RLIMIT_STACK, (max_stack, max_stack))

                except (AttributeError, ValueError, OSError) as e:
                    # Resource limits not available or not permitted on this platform
                    logger.warning("resource_limits_not_applied", error=str(e))

            # On Windows, we'll use different approach for resource limits
            if self.platform.is_windows():
                # Check if required Windows modules are available
                try:
                    import win32job
                    import win32process
                    import win32api

                    # Use Windows job objects to limit resources
                    # Create a job object to limit resources
                    job = win32job.CreateJobObject(None, "")

                    # Set extended limit information
                    extended_info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)

                    # Access BasicLimitInformation correctly
                    basic_limit_info = extended_info['BasicLimitInformation']
                    basic_limit_info['ActiveProcessLimit'] = 1
                    basic_limit_info['PerProcessUserTimeLimit'] = 300000000  # 5 minutes in 100ns units
                    basic_limit_info['MaximumWorkingSetSize'] = self.config.max_memory_mb * 1024 * 1024  # Convert MB to bytes
                    basic_limit_info['MinimumWorkingSetSize'] = 1 * 1024 * 1024  # 1MB

                    # Check if JOB_OBJECT_LIMIT_WORKING_SET is available (some Windows versions don't have it)
                    limit_flags = win32job.JOB_OBJECT_LIMIT_ACTIVE_PROCESS \
                               | win32job.JOB_OBJECT_LIMIT_PROCESS_TIME \
                               | win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

                    # Add working set limit only if it's available
                    if hasattr(win32job, 'JOB_OBJECT_LIMIT_WORKING_SET'):
                        limit_flags |= win32job.JOB_OBJECT_LIMIT_WORKING_SET

                    # Set the limit flags
                    extended_info['LimitFlags'] = limit_flags
                    extended_info['BasicLimitInformation'] = basic_limit_info

                    win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, extended_info)

                    # Create process suspended to assign to job first
                    startup_info = win32process.STARTUPINFO()
                    creation_flags = win32process.CREATE_SUSPENDED | win32process.CREATE_NEW_PROCESS_GROUP

                    proc_handle, thrd_handle, proc_id, thr_id = win32process.CreateProcess(
                        None,  # Application name
                        ' '.join(cmd),  # Command line
                        None,  # Process security attributes
                        None,  # Thread security attributes
                        False,  # Inherit handles
                        creation_flags,  # Creation flags
                        env,  # Environment
                        launch_cwd,  # Current directory
                        startup_info  # Startup info
                    )

                    # Assign process to job
                    win32job.AssignProcessToJobObject(job, proc_handle)

                    # Resume the process
                    win32process.ResumeThread(thrd_handle)

                    # Close handles
                    win32api.CloseHandle(thrd_handle)

                    # Create a subprocess.Popen-like object for compatibility
                    import psutil
                    proc = psutil.Process(proc_id)

                except ImportError:
                    # Fallback to standard subprocess if Windows modules not available
                    logger.warning("windows_job_objects_not_available",
                                 msg="pywin32 not installed, using standard subprocess")
                    proc = subprocess.Popen(
                        cmd,
                        shell=use_shell,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        bufsize=1,  # Line buffered
                        cwd=launch_cwd,
                        env=env,
                        # SECURITY: Prevent spawned processes from inheriting stdin
                        stdin=subprocess.DEVNULL
                    )
            else:
                # Unix-like systems - use resource limits
                proc = subprocess.Popen(
                    cmd,
                    shell=use_shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1,  # Line buffered
                    cwd=launch_cwd,
                    env=env,
                    # SECURITY: Prevent spawned processes from inheriting stdin
                    stdin=subprocess.DEVNULL,
                    # Apply resource limits to child process (Unix only)
                    preexec_fn=apply_resource_limits
                )

            # Instead of creating threads per process, we'll collect all processes
            # and handle output in a single monitoring thread later
            pass  # Output will be handled by the centralized monitor

            if existing:
                existing.proc = proc
                existing.restarts += 1
                existing.status = "running"
                existing.backoff_seconds = self.supervisor.initial_backoff
                return existing
            else:
                info = ProcessInfo(
                    artifact=art,
                    name=name,
                    cmd=cmd,
                    proc=proc,
                    status="running"
                )
                self.processes.append(info)
                self._save_pid(proc.pid if hasattr(proc, 'pid') else proc.pid)
                
                # Publish module start event to Kafka
                if self.kafka_manager:
                    import asyncio
                    asyncio.create_task(
                        self.kafka_manager.publish_module_event('module_started', name, {
                            'pid': proc.pid if hasattr(proc, 'pid') else proc.pid,
                            'command': cmd
                        })
                    )
                
                return info

        except Exception as e:
            logger.error("spawn_failed", artifact=art, error=str(e))
            return None

    def _spawn_processes(self, artifacts: List[Dict[str, Any]]):
        """Spawn all processes from artifacts."""
        logger.info(f"Supervisor: Spawning {len(artifacts)} subprocesses...")
        for art in artifacts:
            self._launch_process(art)

    def _main_loop(self):
        """Main supervision loop using Kafka and Redis for communication."""
        logger.info("EXECUTION STARTED. Press Ctrl+C to abort.")

        if self.kafka_manager:
            logger.info("SUPERVISOR: Using Kafka for reliable messaging.")
        elif self._redis_available:
            logger.info("SUPERVISOR: Using Redis pub/sub for real-time communication.")
        else:
            logger.warning("SUPERVISOR: Both Kafka and Redis unavailable, using polling fallback.")

        # More efficient supervision - reduce frequency of process checks
        # Process supervision is handled by _check_processes() called less frequently
        check_interval = 2.0  # Check every 2 seconds instead of every 1
        last_check = time.time()

        while self.running:
            current_time = time.time()

            # Only check processes every check_interval seconds
            if current_time - last_check >= check_interval:
                self._check_processes()
                last_check = current_time

            # Sleep for a shorter interval to maintain responsiveness
            time.sleep(0.1)

    def _check_processes(self):
        """Check all processes and handle crashes using more efficient monitoring."""
        now = time.time()

        # Use a more efficient approach - only check processes that need attention
        for p_info in self.processes:
            if p_info.proc is None:
                continue

            # Check if in backoff period
            if p_info.status == "backoff":
                if self.supervisor.should_restart_process(p_info):
                    logger.info(f"PHOENIX PROTOCOL: Respawning {p_info.name} after {p_info.backoff_seconds:.1f}s backoff...")
                    self._launch_process(p_info.artifact, existing=p_info)
                continue

            # Check if process has exited (non-blocking check)
            try:
                # For Windows, use psutil to check if process is still alive
                if self.platform.is_windows():
                    import psutil
                    try:
                        proc = p_info.proc
                        # If proc is a psutil Process object
                        if hasattr(proc, 'is_running'):
                            if not proc.is_running():
                                # Process has died
                                ret = proc.status() if proc.status() != 'zombie' else 1
                                self._handle_process_exit(p_info, ret, now)
                        else:
                            # If proc is a subprocess.Popen object
                            ret = p_info.proc.poll()
                            if ret is not None:
                                self._handle_process_exit(p_info, ret, now)
                    except psutil.NoSuchProcess:
                        # Process definitely died
                        self._handle_process_exit(p_info, 1, now)
                else:
                    # Unix-like systems - use poll
                    ret = p_info.proc.poll()
                    if ret is not None:
                        self._handle_process_exit(p_info, ret, now)

            except Exception as e:
                logger.warning("process_check_error", name=p_info.name, error=str(e))
                # Assume process died if we can't check
                self._handle_process_exit(p_info, 1, now)

    def _handle_process_exit(self, p_info, ret, now):
        """Handle a process exit with proper cleanup."""
        p_info.last_crash = now

        if ret == 0:
            logger.info(f"Process {p_info.name} completed successfully.")
            p_info.status = "stopped"
            
            # Publish module stop event to Kafka
            if self.kafka_manager:
                import asyncio
                asyncio.create_task(
                    self.kafka_manager.publish_module_event('module_stopped', p_info.name, {
                        'exit_code': ret
                    })
                )
            return

        logger.error(f"ALERT: Process {p_info.name} died with code {ret}!")

        # Print stderr for debugging if available
        try:
            if hasattr(p_info.proc, 'stderr') and p_info.proc.stderr:
                # Try to read any remaining stderr
                try:
                    err_out = p_info.proc.stderr.read()
                    if err_out:
                        logger.error(f"{p_info.name} STDERR:\n{err_out}")
                except:
                    pass  # May fail if stream is closed
        except:
            pass

        # Use supervisor to handle the crash
        should_restart = self.supervisor.handle_process_crash(p_info, ret)
        if should_restart:
            logger.info(f"Respawning {p_info.name} after backoff period...")
        else:
            # Publish module failure event to Kafka
            if self.kafka_manager:
                import asyncio
                asyncio.create_task(
                    self.kafka_manager.publish_module_event('module_failed', p_info.name, {
                        'exit_code': ret,
                        'restart_attempts': p_info.restarts
                    })
                )

    def get_status(self) -> Dict[str, Any]:
        """Get status of all processes including Kafka and Redis statistics."""
        status = {
            "running": self.running,
            "redis_available": self._redis_available,
            "kafka_available": self.kafka_manager is not None,
            "processes": [
                {
                    "name": p.name,
                    "status": p.status,
                    "restarts": p.restarts,
                    "pid": p.proc.pid if p.proc and hasattr(p.proc, 'pid') else None
                }
                for p in self.processes
            ]
        }

        # Add Redis statistics if available
        if self._redis_available and self.memory:
            try:
                status["redis"] = self.memory.get_stats()
                status["registered_modules"] = self.memory.get_registered_modules()
            except Exception as e:
                logger.warning("redis_stats_failed", error=str(e))
                status["redis"] = {"error": str(e)}
        
        # Add Kafka statistics if available
        if self.kafka_manager:
            try:
                status["kafka"] = {
                    "bootstrap_servers": self.config.kafka_bootstrap_servers,
                    "topics": self.config.kafka_topics
                }
            except Exception as e:
                logger.warning("kafka_stats_failed", error=str(e))
                status["kafka"] = {"error": str(e)}

        return status

    def shutdown(self, timeout: float = 5.0):
        """Graceful shutdown with timeout."""
        self.running = False
        logger.info("Initiating graceful shutdown...")

        # Unregister from Redis and close connections
        if self._redis_available and self.memory:
            try:
                logger.info("Unregistering orchestrator from Redis...")
                self.memory.unregister_module('orchestrator')
                self.memory.close()
                logger.info("Redis connections closed.")
            except Exception as e:
                logger.warning("redis_shutdown_error", error=str(e))
        
        # Close Kafka connections
        if self.kafka_manager:
            try:
                logger.info("Closing Kafka connections...")
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.kafka_manager.stop_producer())
                logger.info("Kafka connections closed.")
            except Exception as e:
                logger.warning("kafka_shutdown_error", error=str(e))

        # Terminate all processes with proper cleanup
        for p_info in self.processes:
            if p_info.proc is None:
                continue

            try:
                logger.info(f"Terminating {p_info.name}...")

                # First try graceful termination
                if hasattr(p_info.proc, 'terminate'):
                    p_info.proc.terminate()
                else:
                    # For psutil Process objects
                    try:
                        p_info.proc.terminate()
                    except:
                        pass

                try:
                    # Wait for graceful termination
                    if hasattr(p_info.proc, 'wait'):
                        exit_code = p_info.proc.wait(timeout=timeout)
                        logger.info(f"{p_info.name} terminated gracefully with exit code {exit_code}.")
                    else:
                        # For psutil Process objects
                        p_info.proc.wait(timeout=timeout)
                        logger.info(f"{p_info.name} terminated gracefully.")
                except subprocess.TimeoutExpired:
                    logger.warning(f"{p_info.name} didn't respond, forcing termination...")
                    try:
                        # Force kill the process
                        if hasattr(p_info.proc, 'kill'):
                            p_info.proc.kill()
                        else:
                            # For psutil Process objects
                            p_info.proc.kill()
                        # Wait briefly for the process to be cleaned up
                        if hasattr(p_info.proc, 'wait'):
                            p_info.proc.wait(timeout=1)
                    except:
                        # Process may have already exited
                        pass

            except ProcessLookupError:
                # Process already terminated
                logger.info(f"{p_info.name} already terminated.")
            except Exception as e:
                logger.error("shutdown_error", name=p_info.name, error=str(e))

        # Wait for the output monitoring thread to finish
        if self._output_monitor_thread and self._output_monitor_thread.is_alive():
            self._output_monitor_thread.join(timeout=2.0)

        # Clean up PID files and temporary resources
        self._cleanup_pid_files()
        self._cleanup_temp_resources()

        logger.info("System Shutdown Complete. All resources cleaned up.")

    def _cleanup_pid_files(self):
        """Remove PID files created during execution."""
        pid_dir = ".qyro"
        if os.path.exists(pid_dir):
            pid_file = os.path.join(pid_dir, "pids")
            if os.path.exists(pid_file):
                try:
                    os.remove(pid_file)
                    logger.debug("pid_file_removed", path=pid_file)
                except Exception as e:
                    logger.warning("pid_file_remove_failed", path=pid_file, error=str(e))

    def _cleanup_temp_resources(self):
        """Clean up temporary files and resources."""
        # Clean up any temporary files created during execution
        import glob
        temp_patterns = [
            "QYRO_*.tmp",
            "*.tmp",
            ".QYRO_*.lock",
            "QYRO_generated/*",
        ]

        for pattern in temp_patterns:
            for temp_file in glob.glob(pattern):
                try:
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                        logger.debug("temp_file_removed", path=temp_file)
                    elif os.path.isdir(temp_file):
                        import shutil
                        shutil.rmtree(temp_file)
                        logger.debug("temp_dir_removed", path=temp_file)
                except Exception as e:
                    logger.warning("temp_resource_remove_failed", path=temp_file, error=str(e))

        # Clean up any temporary directories
        temp_dirs = [".QYRO_tmp", "__pycache__", "QYRO_generated"]
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.debug("temp_dir_removed", path=temp_dir)
                except Exception as e:
                    logger.warning("temp_dir_remove_failed", path=temp_dir, error=str(e))

    def broadcast_to_all(self, message: Dict[str, Any]) -> bool:
        """
        Broadcast a message to all modules via Kafka.

        Args:
            message: Dictionary containing the message to broadcast

        Returns:
            True if broadcast was successful, False otherwise
        """
        if not self.kafka_manager:
            logger.warning("broadcast_failed", reason="kafka_unavailable")
            return False

        try:
            import uuid
            broadcast_id = str(uuid.uuid4())
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.kafka_manager.broadcast_message(message, broadcast_id))
            logger.debug("message_broadcast", message=message)
            return True
        except Exception as e:
            logger.error("broadcast_error", error=str(e))
            return False

    def antigravity_protocol(self, error: Exception):
        """Handle critical errors."""
        try:
            logger.error(f"CRITICAL ERROR: {error}")
        except UnicodeEncodeError:
            encoding = getattr(sys.stdout, 'encoding', 'utf-8') or 'utf-8'
            safe_err = str(error).encode(encoding, errors='replace').decode(encoding)
            logger.error(f"CRITICAL ERROR: {safe_err}")

        logger.critical("antigravity_protocol", error=str(error))
        self.shutdown()
        sys.exit(1)

    def _safe_print(self, message: str):
        """Thread-safe and encoding-safe print."""
        try:
            print(message, flush=True)
        except UnicodeEncodeError:
            encoding = getattr(sys.stdout, 'encoding', 'utf-8') or 'utf-8'
            safe_msg = message.encode(encoding, errors='replace').decode(encoding)
            print(safe_msg, flush=True)

    def _save_pid(self, pid: int):
        """Save a PID to the active PIDs file."""
        pid_file = ".qyro/pids"
        os.makedirs(".qyro", exist_ok=True)
        with open(pid_file, "a") as f:
            f.write(f"{pid}\n")

    def _cleanup_stale_processes(self):
        """Kill stale processes using persisted PIDs from previous runs."""
        pid_file = ".qyro/pids"
        if not os.path.exists(pid_file):
            return

        logger.info("Cleaning up stale processes from previous run...")
        try:
            with open(pid_file, "r") as f:
                pids = [line.strip() for line in f.readlines() if line.strip()]

            for pid_str in pids:
                try:
                    pid = int(pid_str)
                    # Try to terminate
                    self.platform.kill_process(pid, force=True)
                except:
                    pass

            # Clear the file
            os.remove(pid_file)
        except Exception as e:
            logger.warning("cleanup_stale_processes_failed", error=str(e))

    def _prepare_frontend(self, framework: str):
        """Prepare frontend environment with manual package.json to avoid CRA conflicts."""
        cwd = "QYRO_frontend"
        if not os.path.exists(cwd):
            os.makedirs(cwd)

        # Manually create a minimal Vite + React + TS project structure
        pkg_json_path = os.path.join(cwd, "package.json")
        if not os.path.exists(pkg_json_path):
            logger.info(f"Frontend: Initializing {framework} project structure...")

            pkg_json = {
                "name": "nexus-frontend",
                "private": True,
                "version": "0.0.0",
                "type": "module",
                "scripts": {
                    "dev": "vite",
                    "build": "tsc && vite build",
                    "preview": "vite preview",
                    "start": "vite"
                },
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "nexus-react": "file:../qyro/adapters/language_adapters/node_adapter",
                    "lucide-react": "^0.300.0"
                },
                "devDependencies": {
                    "@types/react": "^18.2.0",
                    "@types/react-dom": "^18.2.0",
                    "@vitejs/plugin-react": "^4.0.0",
                    "typescript": "^5.0.0",
                    "vite": "^4.3.0"
                }
            }
            import json
            with open(pkg_json_path, 'w') as f:
                json.dump(pkg_json, f, indent=2)

            # Create vite.config.ts
            with open(os.path.join(cwd, "vite.config.ts"), 'w') as f:
                f.write("""
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: { port: 3000 }
})
""")

            # Create index.html
            with open(os.path.join(cwd, "index.html"), 'w') as f:
                f.write("""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Nexus UI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""")

            # Create src/main.tsx
            os.makedirs(os.path.join(cwd, "src"), exist_ok=True)
            with open(os.path.join(cwd, "src", "main.tsx"), 'w') as f:
                f.write("""
import React from 'react'
import ReactDOM from 'react-dom/client'
import NexusComponent from './NexusComponent'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <NexusComponent />
  </React.StrictMode>,
)
""")

            # Create empty index.css
            with open(os.path.join(cwd, "src", "index.css"), 'w') as f:
                f.write("body { margin: 0; font-family: sans-serif; background: #0f172a; color: white; }")

        # Always check for node_modules
        if not os.path.exists(os.path.join(cwd, "node_modules")):
            logger.info("Frontend: Installing dependencies... (First time only)")
            subprocess.run(["npm", "install"], cwd=cwd, shell=True)

    def _print_banner(self):
        banner = r"""
  _   _ ________   __  _______  _____
 | \ | |  ____\ \ / / |__   __||_   _|
 |  \| | |__   \ V /     | |     | |
 | . ` |  __|   > <      | |     | |
 | |\  | |____ / . \     | |    _| |_
 |_| \_|______/_/ \_\    |_|   |_____|
        """
        print(f"{Fore.GREEN}{banner}{Style.RESET_ALL}", flush=True)
        print(f"{Fore.CYAN}  Polyglot Runtime v2.0 - NBP v3 Protocol{Style.RESET_ALL}", flush=True)
        print(flush=True)
