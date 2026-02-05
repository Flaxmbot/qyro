"""
Nexus Builder
Handles building and packaging Nexus applications for different deployment targets.
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

from .parser import NexusParser
from .compiler import NexusCompiler
from .logging import get_logger


logger = get_logger("nexus.builder")


@dataclass
class BuildConfig:
    """Configuration for building Nexus applications."""
    output_dir: str = "./dist"
    target: str = "docker"  # docker, binary, kubernetes
    include_dependencies: bool = True
    optimize: bool = True
    debug: bool = False


class NexusBuilder:
    """Builds Nexus applications for deployment."""
    
    def __init__(self, nexus_file: str, output_dir: str = "./dist", target: str = "docker"):
        self.nexus_file = nexus_file
        self.output_dir = Path(output_dir)
        self.target = target
        self.parser = NexusParser()
        self.compiler = NexusCompiler()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized builder for {nexus_file} targeting {target}")

    def build(self):
        """Build the Nexus application."""
        logger.info(f"Starting build for {self.nexus_file} targeting {self.target}")
        
        # Parse the Nexus file
        logger.info("Parsing Nexus file...")
        self.parser.parse_file(self.nexus_file)
        
        # Compile artifacts
        logger.info("Compiling artifacts...")
        artifacts = self.compiler.compile(self.parser.blocks)
        
        # Build based on target
        if self.target == "docker":
            self._build_docker(artifacts)
        elif self.target == "binary":
            self._build_binary(artifacts)
        elif self.target == "kubernetes":
            self._build_kubernetes(artifacts)
        else:
            raise ValueError(f"Unsupported target: {self.target}")
        
        logger.info(f"Build completed successfully in {self.output_dir}")

    def _build_docker(self, artifacts: List[Dict[str, Any]]):
        """Build Docker images for each artifact."""
        logger.info("Building Docker images...")
        
        # Create Dockerfile for each language
        dockerfiles = {
            'py': self._create_python_dockerfile(),
            'rs': self._create_rust_dockerfile(),
            'c': self._create_c_dockerfile(),
            'java': self._create_java_dockerfile(),
        }
        
        # Write Dockerfiles
        for lang, dockerfile_content in dockerfiles.items():
            dockerfile_path = self.output_dir / f"Dockerfile.{lang}"
            dockerfile_path.write_text(dockerfile_content)
        
        # Build a combined image
        combined_dockerfile = self._create_combined_dockerfile(artifacts)
        combined_path = self.output_dir / "Dockerfile"
        combined_path.write_text(combined_dockerfile)
        
        # Build the image
        image_tag = f"nexus-app:{Path(self.nexus_file).stem}"
        subprocess.run([
            "docker", "build", 
            "-t", image_tag,
            "-f", str(combined_path),
            str(self.output_dir.parent)
        ], check=True)
        
        logger.info(f"Docker image built: {image_tag}")

    def _create_python_dockerfile(self) -> str:
        """Create Dockerfile for Python modules."""
        return """# Dockerfile for Nexus Python modules
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r nexus && useradd -r -g nexus nexus

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Change ownership
RUN chown -R nexus:nexus /app
USER nexus

EXPOSE 8000 8765

CMD ["python", "run.py", "/app/main.nexus"]
"""

    def _create_rust_dockerfile(self) -> str:
        """Create Dockerfile for Rust modules."""
        return """# Dockerfile for Nexus Rust modules
FROM rust:1.70-alpine as builder

# Install system dependencies
RUN apk add --no-cache musl-dev

WORKDIR /app

# Copy source and build
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release

FROM alpine:latest

# Create non-root user
RUN addgroup -g 1001 -S nexus && \\
    addgroup -S nexus && \\
    adduser -S nexus -u 1001 -G nexus

# Install runtime dependencies
RUN apk add --no-cache ca-certificates

WORKDIR /root/

# Copy binary from builder stage
COPY --from=builder /app/target/release/nexus_app ./nexus_app

# Change ownership
RUN chown nexus:nexus ./nexus_app
USER nexus

EXPOSE 8000 8765

CMD ["./nexus_app"]
"""

    def _create_c_dockerfile(self) -> str:
        """Create Dockerfile for C modules."""
        return """# Dockerfile for Nexus C modules
FROM alpine:latest as builder

# Install build dependencies
RUN apk add --no-cache \\
    build-base \\
    linux-headers

WORKDIR /app

# Copy source files
COPY . .

# Compile C programs
RUN gcc -o main main.c

FROM alpine:latest

# Create non-root user
RUN addgroup -g 1001 -S nexus && \\
    addgroup -S nexus && \\
    adduser -S nexus -u 1001 -G nexus

# Install runtime dependencies
RUN apk add --no-cache libc6-compat

WORKDIR /root/

# Copy binary from builder stage
COPY --from=builder /app/main ./main

# Change ownership
RUN chown nexus:nexus ./main
USER nexus

EXPOSE 8000 8765

CMD ["./main"]
"""

    def _create_java_dockerfile(self) -> str:
        """Create Dockerfile for Java modules."""
        return """# Dockerfile for Nexus Java modules
FROM maven:3.8.6-openjdk-17 AS build

WORKDIR /app

# Copy Maven files
COPY pom.xml .
COPY src ./src

# Build JAR
RUN mvn clean package -DskipTests

FROM openjdk:17-jre-slim

# Create non-root user
RUN groupadd -r nexus && useradd -r -g nexus nexus

WORKDIR /app

# Copy JAR from build stage
COPY --from=build /app/target/*.jar app.jar

# Change ownership
RUN chown nexus:nexus app.jar
USER nexus

EXPOSE 8000 8765

CMD ["java", "-jar", "app.jar"]
"""

    def _create_combined_dockerfile(self, artifacts: List[Dict[str, Any]]) -> str:
        """Create a combined Dockerfile for all artifacts."""
        # Determine required base images based on artifacts
        langs = {artifact['type'] for artifact in artifacts if artifact['type'] in ['py', 'rs', 'c', 'java']}
        
        dockerfile_parts = [
            "# Multi-stage Dockerfile for Nexus application",
            "FROM python:3.11-slim AS nexus-base",
            "",
            "# Create non-root user",
            "RUN groupadd -r nexus && useradd -r -g nexus nexus",
            "",
            "# Install common dependencies",
            "RUN apt-get update && apt-get install -y --no-install-recommends \\",
            "    curl \\",
            "    ca-certificates \\",
            "    && rm -rf /var/lib/apt/lists/* \\",
            "    && apt-get clean",
            "",
            "WORKDIR /app",
            ""
        ]
        
        # Add installation for each language
        if 'py' in langs:
            dockerfile_parts.extend([
                "# Python dependencies",
                "COPY requirements.txt .",
                "RUN pip install --no-cache-dir -r requirements.txt",
                ""
            ])
        
        if 'rs' in langs:
            dockerfile_parts.extend([
                "# Install Rust if needed",
                "RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
                "ENV PATH=\"/root/.cargo/bin:${PATH}\"",
                ""
            ])
        
        if 'c' in langs:
            dockerfile_parts.extend([
                "# Install C build tools if needed",
                "RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ \\",
                "    && rm -rf /var/lib/apt/lists/*",
                ""
            ])
        
        if 'java' in langs:
            dockerfile_parts.extend([
                "# Install OpenJDK if needed",
                "RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jdk \\",
                "    && rm -rf /var/lib/apt/lists/*",
                ""
            ])
        
        # Copy application files
        dockerfile_parts.extend([
            "# Copy application files",
            "COPY . .",
            "",
            "# Change ownership",
            "RUN chown -R nexus:nexus /app",
            "USER nexus",
            "",
            "EXPOSE 8000 8765",
            "",
            "CMD [\"python\", \"run.py\", \"main.nexus\"]"
        ])
        
        return "\n".join(dockerfile_parts)

    def _build_binary(self, artifacts: List[Dict[str, Any]]):
        """Build standalone binary distributions."""
        logger.info("Building binary distribution...")
        
        # Create bin directory
        bin_dir = self.output_dir / "bin"
        bin_dir.mkdir(exist_ok=True)
        
        # Copy compiled binaries
        for artifact in artifacts:
            if artifact['type'] in ['c', 'rs', 'go']:
                src_bin = Path(artifact['bin'])
                if src_bin.exists():
                    dest_bin = bin_dir / src_bin.name
                    shutil.copy2(src_bin, dest_bin)
                    logger.info(f"Copied binary: {src_bin} -> {dest_bin}")
        
        # Create a launcher script
        launcher_script = self.output_dir / "nexus-launcher.sh"
        launcher_script.write_text(f"""#!/bin/bash
# Nexus Application Launcher

# Set up environment
export NEXUS_ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
export PATH="$NEXUS_ROOT/bin:$PATH"

# Launch the application
python run.py main.nexus "$@"
""")
        
        # Make executable
        launcher_script.chmod(0o755)

    def _build_kubernetes(self, artifacts: List[Dict[str, Any]]):
        """Build Kubernetes deployment configuration."""
        logger.info("Building Kubernetes configuration...")
        
        # Create k8s directory
        k8s_dir = self.output_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)
        
        # Generate Kubernetes YAML
        k8s_yaml = self._generate_k8s_config(artifacts)
        
        # Write to file
        k8s_file = k8s_dir / "deployment.yaml"
        k8s_file.write_text(k8s_yaml)
        
        logger.info(f"Kubernetes configuration written to {k8s_file}")

    def _generate_k8s_config(self, artifacts: List[Dict[str, Any]]) -> str:
        """Generate Kubernetes deployment configuration."""
        # Determine services based on artifacts
        services = []
        deployments = []
        
        # Base deployment for orchestrator
        deployments.append({
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "nexus-orchestrator",
                "labels": {"app": "nexus-orchestrator"}
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "nexus-orchestrator"}},
                "template": {
                    "metadata": {"labels": {"app": "nexus-orchestrator"}},
                    "spec": {
                        "containers": [{
                            "name": "orchestrator",
                            "image": f"nexus-app:{Path(self.nexus_file).stem}",
                            "ports": [
                                {"containerPort": 8000, "name": "web"},
                                {"containerPort": 8765, "name": "gateway"}
                            ],
                            "env": [
                                {"name": "KAFKA_BOOTSTRAP_SERVERS", "value": "kafka:9092"},
                                {"name": "REDIS_HOST", "value": "redis:6379"}
                            ]
                        }]
                    }
                }
            }
        })
        
        # Services
        services.append({
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "nexus-orchestrator"},
            "spec": {
                "selector": {"app": "nexus-orchestrator"},
                "ports": [
                    {"protocol": "TCP", "port": 8000, "targetPort": 8000, "name": "web"},
                    {"protocol": "TCP", "port": 8765, "targetPort": 8765, "name": "gateway"}
                ]
            }
        })
        
        # Combine everything
        all_resources = deployments + services
        
        # Convert to YAML
        yaml_lines = []
        for i, resource in enumerate(all_resources):
            if i > 0:
                yaml_lines.append("---")
            yaml_lines.append("# Generated Kubernetes configuration for Nexus application")
            yaml_lines.append(json.dumps(resource, indent=2))
        
        return "\n".join(yaml_lines)