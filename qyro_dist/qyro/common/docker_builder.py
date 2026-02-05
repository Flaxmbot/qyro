import os
import shutil
from typing import Dict, List, Any
from pathlib import Path

class QyroDockerBuilder:
    def __init__(self, qyro_file: str, output_dir: str = "qyro_dist"):
        self.qyro_file = qyro_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.modules_dir = self.output_dir / "modules"
        self.modules_dir.mkdir(exist_ok=True)

    def build(self, named_blocks: Dict[str, List[Dict[str, Any]]]):
        """
        Generate Docker configuration and source files.
        named_blocks: result from parser.get_named_blocks()
        """
        print(f"[QYRO] Generating Docker build context in {self.output_dir}...")

        # 0. Copy Qyro Library to build context
        self._copy_qyro_lib()

        # 1. Generate Source Files & Dependency Manifests
        deps = self._process_blocks(named_blocks)

        # 2. Generate Dockerfile
        self._generate_dockerfile(deps)

        # 3. Generate docker-compose.yml
        self._generate_compose()

        print(f"[QYRO] Build context generated successfully.")

    def _copy_qyro_lib(self):
        """Copy the qyro library to the build context."""
        try:
            import qyro
            package_path = os.path.dirname(qyro.__file__)
            # Copy to qyro_dist/qyro
            dest = self.output_dir / "qyro"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(package_path, dest)
            print(f"[QYRO] Copied library to build context.")
        except Exception as e:
            print(f"[QYRO] Warning: Could not copy qyro library: {e}")

    def _process_blocks(self, blocks: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Write code blocks to files and collect dependencies.
        Returns a dict of dependencies per language.
        """
        deps = {
            'python': set(),
            'rust': set(),
            'go': set(),
            'node': set(),
            'java': set()
        }

        # Python
        for block in blocks.get('python', []) + blocks.get('py', []):
            name = block['name']
            content = block['content']
            deps['python'].update(block.get('dependencies', []))

            # Write file
            file_path = self.modules_dir / f"{name}.py"
            with open(file_path, 'w') as f:
                f.write(content)

        # AI Agents
        for block in blocks.get('agent', []):
            name = block['name']
            content = block['content']
            deps['python'].update(block.get('dependencies', [])) # Agents are Python-based

            # Inject adapter import
            injected_code = "from qyro.adapters.language_adapters.agent.agent_adapter import init, on, _agent_instance\n" + content

            file_path = self.modules_dir / f"{name}_agent.py"
            with open(file_path, 'w') as f:
                f.write(injected_code)

        # Rust
        for block in blocks.get('rust', []) + blocks.get('rs', []):
            name = block['name']
            content = block['content']
            deps['rust'].update(block.get('dependencies', []))

            # Write file (assuming single file modules for now)
            # Create subfolder for rust module
            rs_dir = self.modules_dir / name
            rs_dir.mkdir(exist_ok=True)
            with open(rs_dir / "main.rs", 'w') as f:
                f.write(content)

        # Go
        for block in blocks.get('go', []):
            name = block['name']
            content = block['content']
            deps['go'].update(block.get('dependencies', []))

            go_dir = self.modules_dir / name
            go_dir.mkdir(exist_ok=True)
            with open(go_dir / "main.go", 'w') as f:
                f.write(content)

        # Java
        for block in blocks.get('java', []):
            name = block['name']
            content = block['content']
            deps['java'].update(block.get('dependencies', []))

            # Extract class name if possible
            import re
            class_match = re.search(r'public\s+class\s+(\w+)', content)
            class_name = class_match.group(1) if class_match else name

            java_dir = self.modules_dir / name
            java_dir.mkdir(exist_ok=True)
            with open(java_dir / f"{class_name}.java", 'w') as f:
                f.write(content)

        # Web/Node
        for block in blocks.get('node', []) + blocks.get('ts', []) + blocks.get('js', []):
            name = block['name']
            content = block['content']
            deps['node'].update(block.get('dependencies', []))

            node_dir = self.modules_dir / name
            node_dir.mkdir(exist_ok=True)
            ext = 'ts' if block['original_type'].startswith('ts') else 'js'
            with open(node_dir / f"index.{ext}", 'w') as f:
                f.write(content)

        # React/Web (Special case, usually separate container or served static)
        # For simplicity, we treat them as Node modules for now or rely on `qyro run` handling
        # But user wants "run on docker".
        # We'll skip complex React build inside this container for now and assume simple script execution

        return deps

    def _generate_dockerfile(self, deps: Dict[str, Any]):
        """Generate a multi-stage Dockerfile."""

        # Base image: Universal Qyro Image
        # We'll use a fat image or multi-stage to install all tools.
        # To make it "easy", we'll use a single image based on Python that installs other tools.
        # Or better: Multi-stage build that compiles Rust/Go/Java then copies to a runtime image.

        dockerfile = [
            "FROM python:3.11-slim-bookworm",
            "WORKDIR /app",

            "# --- System Dependencies ---",
            "RUN apt-get update && apt-get install -y --no-install-recommends \\",
            "    curl build-essential git openjdk-17-jdk maven \\",
            "    && rm -rf /var/lib/apt/lists/*",

            "# --- Rust Setup ---",
            "ENV RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/usr/local/cargo PATH=/usr/local/cargo/bin:$PATH",
            "RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",

            "# --- Go Setup ---",
            "COPY --from=golang:1.21 /usr/local/go /usr/local/go",
            "ENV PATH=$PATH:/usr/local/go/bin",

            "# --- Node.js Setup ---",
            "RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs",

            "# --- Qyro Library ---",
            "# Build context is qyro_dist, so paths are relative to that directory",
            "COPY qyro /app/qyro",
            "ENV PYTHONPATH=/app",

            "# Build Java Client",
            "WORKDIR /app/qyro/adapters/language_adapters/java",
            "RUN mvn install -q",
            "WORKDIR /app",

            "# --- Python Dependencies ---"
        ]

        # Python Deps
        py_deps = sorted(list(deps['python']))
        py_deps.extend(["redis", "confluent-kafka", "rich", "pydantic", "docker", "click"]) # Core deps

        with open(self.output_dir / "requirements.txt", 'w') as f:
            f.write("\n".join(py_deps))

        dockerfile.extend([
            "COPY requirements.txt .",
            "RUN pip install -r requirements.txt",

            "# --- Application Source ---",
            "COPY modules /app/modules",

            "# --- Entrypoint ---",
            "CMD [\"python\", \"-m\", \"qyro.cli.cli\", \"run-internal\"]"
        ])
        with open(self.output_dir / "Dockerfile", 'w') as f:
            f.write("\n".join(dockerfile))

    def _generate_compose(self):
        compose = '''services:
  qyro-app:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/app
    ports:
      - "8000:8000"
      - "3000:3000"
    environment:
      - QYRO_REDIS_HOST=redis
      - QYRO_REDIS_PORT=6379
      - QYRO_KAFKA_BOOTSTRAP_SERVERS=kafka:29092
      - PYTHONUNBUFFERED=1
    depends_on:
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    networks:
      - qyro-network
    restart: unless-stopped
    tty: true

  redis:
    image: redis:7-alpine
    container_name: qyro-redis
    ports:
      - "6379:6379"
    networks:
      - qyro-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: qyro-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    networks:
      - qyro-network
    healthcheck:
      test: ["CMD", "bash", "-c", "echo stat | nc localhost 2181 | grep -q 'Mode:'"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 60s

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: qyro-kafka
    depends_on:
      zookeeper:
        condition: service_healthy
    ports:
      - "9092:9092"
      - "29092:29092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    networks:
      - qyro-network
    healthcheck:
      test: ["CMD", "bash", "-c", "kafka-broker-api-versions.sh --bootstrap-server localhost:9092 | grep -q '3.5'"]
      interval: 30s
      timeout: 15s
      retries: 10
      start_period: 120s

networks:
  qyro-network:
    driver: bridge
'''
        with open(self.output_dir / "docker-compose.yml", 'w') as f:
            f.write(compose)
