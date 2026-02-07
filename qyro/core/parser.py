import re
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
import qyro.lib
from qyro.core.templates import *

class ServiceBlock(BaseModel):
    language: str
    name: str
    dependencies: List[str]
    content: str
    start_line: int

class QyroParser:
    # Support both old syntax (>>>) and new syntax (language:component [dependencies])
    BLOCK_REGEX = re.compile(r"^(?:>>>)?(?P<lang>\w+):(?P<name>[\w-]+)(?:\s*\[(?P<deps>.*)\])?")

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.content = self.filepath.read_text()
        self.services: List[ServiceBlock] = []

    def parse(self):
        lines = self.content.splitlines()
        current_block: Optional[ServiceBlock] = None
        buffer = []

        for i, line in enumerate(lines):
            match = self.BLOCK_REGEX.match(line.strip())
            if match:
                if current_block:
                    current_block.content = "\n".join(buffer).strip()
                    self.services.append(current_block)
                    buffer = []

                lang = match.group("lang")
                name = match.group("name")
                deps_str = match.group("deps")
                deps = [d.strip() for d in deps_str.split(",") if d.strip()] if deps_str else []

                current_block = ServiceBlock(
                    language=lang,
                    name=name,
                    dependencies=deps,
                    content="",
                    start_line=i + 1
                )
            else:
                if current_block:
                    buffer.append(line)

        if current_block:
            current_block.content = "\n".join(buffer).strip()
            self.services.append(current_block)

        return self.services

    def generate_artifacts(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        services_config = []

        for service in self.services:
            service_dir = output_dir / service.name
            service_dir.mkdir(exist_ok=True)

            # Copy language-specific adapters
            self._copy_adapters(service_dir)

            if service.language == "python":
                self._generate_python(service, service_dir)
                services_config.append(self._get_docker_config(service, "python"))
            elif service.language in ["web", "js", "ts"]:
                self._generate_web(service, service_dir)
                services_config.append(self._get_docker_config(service, "node"))
            elif service.language == "rust":
                self._generate_rust(service, service_dir)
                services_config.append(self._get_docker_config(service, "rust"))
            elif service.language == "java":
                self._generate_java(service, service_dir)
                services_config.append(self._get_docker_config(service, "java"))
            elif service.language == "go":
                self._generate_go(service, service_dir)
                services_config.append(self._get_docker_config(service, "go"))
            elif service.language in ["c", "cpp"]:
                self._generate_c(service, service_dir)
                services_config.append(self._get_docker_config(service, "c"))
            else:
                raise ValueError(f"Unsupported language: {service.language}")

        return services_config

    def _copy_adapters(self, dest_dir: Path):
        """Copies qyro adapters to the build context."""
        adapters_src = Path(qyro.lib.__file__).parent
        adapters_dest = dest_dir / "qyro_adapters"
        if adapters_dest.exists():
            shutil.rmtree(adapters_dest)
        shutil.copytree(adapters_src, adapters_dest)

    def _generate_python(self, service: ServiceBlock, path: Path):
        (path / "main.py").write_text(service.content)

        # Inject standard deps
        deps = set(service.dependencies)
        deps.update(["redis", "kafka-python", "requests"])
        reqs = "\n".join(sorted(deps))
        (path / "requirements.txt").write_text(reqs)

        # Create Dockerfile using the universal template
        dockerfile_content = DOCKERFILE_UNIVERSAL_PYTHON.format(filename="main.py")
        (path / "Dockerfile").write_text(dockerfile_content)

    def _generate_web(self, service: ServiceBlock, path: Path):
        is_next = "next" in service.dependencies

        deps_dict = {d: "*" for d in service.dependencies}
        deps_dict.update({
            "axios": "^1.0.0",
            "ioredis": "^5.3.0",
            "kafkajs": "^2.2.0"
        })

        if is_next:
            deps_dict.update({"next": "latest", "react": "latest", "react-dom": "latest"})
            scripts = {"dev": "next dev", "build": "next build", "start": "next start"}
        else:
            deps_dict.update({"react": "^18.0.0", "react-dom": "^18.0.0", "react-scripts": "5.0.1"})
            scripts = {"start": "react-scripts start", "build": "react-scripts build"}

        import json
        pkg = {
            "name": service.name,
            "version": "0.1.0",
            "private": True,
            "dependencies": deps_dict,
            "scripts": scripts,
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
            }
        }
        (path / "package.json").write_text(json.dumps(pkg, indent=2))

        if is_next:
            (path / "pages").mkdir(exist_ok=True)
            (path / "pages" / "index.js").write_text(service.content)
        else:
            (path / "src").mkdir(exist_ok=True)
            (path / "public").mkdir(exist_ok=True)
            (path / "src" / "App.js").write_text(service.content)
            (path / "src" / "index.js").write_text("""
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
""")
            (path / "public" / "index.html").write_text("""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Qyro App</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
""")

        # Create Dockerfile using the universal template
        dockerfile_content = DOCKERFILE_UNIVERSAL_NODE
        (path / "Dockerfile").write_text(dockerfile_content)

    def _generate_rust(self, service: ServiceBlock, path: Path):
        deps_lines = ""
        user_deps = set(service.dependencies)
        # Add defaults
        defaults = {
            "redis": "\"0.23\"",
            "rdkafka": "\"0.29\"",
            "serde": '{ version = "1.0", features = ["derive"] }',
            "serde_json": "\"1.0\"",
            "tokio": '{ version = "1", features = ["full"] }'
        }

        for d, v in defaults.items():
            if d not in user_deps:
                deps_lines += f'{d} = {v}\n'

        for d in user_deps:
            deps_lines += f'{d} = "*"\n'

        cargo_toml = f"""
[package]
name = "{service.name}"
version = "0.1.0"
edition = "2021"

[dependencies]
{deps_lines}
"""
        (path / "Cargo.toml").write_text(cargo_toml)

        (path / "src").mkdir(exist_ok=True)
        (path / "src" / "main.rs").write_text(service.content)

        # Create Dockerfile using the universal template
        dockerfile_content = DOCKERFILE_UNIVERSAL_RUST.format(bin_name=service.name)
        (path / "Dockerfile").write_text(dockerfile_content)

    def _generate_java(self, service: ServiceBlock, path: Path):
        # We need to add dependencies to pom.xml
        dependencies = """
        <dependency>
            <groupId>redis.clients</groupId>
            <artifactId>jedis</artifactId>
            <version>4.3.1</version>
        </dependency>
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>kafka-clients</artifactId>
            <version>3.4.0</version>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.14.2</version>
        </dependency>
        """
        # User deps? We assume they are just names for now, can't easily map to maven coords without a lookup DB.

        pom = f"""
<project xmlns="http://maven.apache.org/POM/4.0.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.qyro.app</groupId>
    <artifactId>{service.name}</artifactId>
    <version>1.0-SNAPSHOT</version>
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
    <dependencies>
        {dependencies}
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.2.4</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                        <configuration>
                            <transformers>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                    <mainClass>com.qyro.app.Main</mainClass>
                                </transformer>
                            </transformers>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
"""
        (path / "pom.xml").write_text(pom)

        # Package structure com.qyro.app
        src_path = path / "src" / "main" / "java" / "com" / "qyro" / "app"
        src_path.mkdir(parents=True, exist_ok=True)
        (src_path / "Main.java").write_text(service.content)

        # Copy Qyro adapters to the service's source directory
        adapters_src = Path(qyro.lib.__file__).parent
        adapters_dest = path / "src" / "main" / "java" / "com" / "qyro" / "adapters"
        adapters_dest.mkdir(parents=True, exist_ok=True)
        import shutil
        for file in adapters_src.glob("*.java"):
            shutil.copy(file, adapters_dest)

        # Create Dockerfile using the Java-specific base image
        dockerfile_content = DOCKERFILE_JAVA
        (path / "Dockerfile").write_text(dockerfile_content)

    def _get_docker_config(self, service: ServiceBlock, type: str):
        # Use port manager for dynamic port assignment
        from qyro.core.port_manager import find_available_port, DEFAULT_PORTS
        
        # Get appropriate port for this service type
        default_port = DEFAULT_PORTS.get(type, 8000)
        if type == "node":
            default_port = 3000
        elif type == "python":
            default_port = 8000
        elif type == "java":
            default_port = 8080
        elif type == "rust":
            default_port = 8081
        elif type == "go":
            default_port = 8082
        elif type == "c":
            default_port = 9000
        
        # Check if we have a stored port assignment, otherwise find available
        if not hasattr(self, '_port_assignments'):
            self._port_assignments = {}
        
        if service.name not in self._port_assignments:
            available_port = find_available_port(type, default_port)
            self._port_assignments[service.name] = available_port
        
        port = self._port_assignments[service.name]
        
        config = f"""
  {service.name}:
    build: ./{service.name}
    networks:
      - qyro-net
    depends_on:
      - redis
      - kafka
"""
        if type == "node":
            config += f"""
    ports:
      - "{port}:3000"
    stdin_open: true
    tty: true
    environment:
      - REACT_APP_API_PORT=${{API_PORT:-8000}}
"""
        elif type == "python":
            # Heuristic: expose 8000 if it looks like a web service
            if any(d in service.dependencies for d in ["fastapi", "flask", "django", "uvicorn"]):
                config += f"""
    ports:
      - "{port}:8000"
"""
        elif type == "java":
            config += f"""
    ports:
      - "{port}:8080"
"""
        elif type == "rust":
            config += f"""
    ports:
      - "{port}:8081"
"""
        elif type == "go":
            config += f"""
    ports:
      - "{port}:8080"
"""
        elif type == "c":
            config += f"""
    ports:
      - "{port}:9000"
"""
        return config

    def _generate_go(self, service: ServiceBlock, path: Path):
        """Generate Go service artifacts."""
        (path / "main.go").write_text(service.content)

        # Create go.mod
        go_mod = f"""module {service.name}

go 1.21

require (
    github.com/go-redis/redis/v8 v8.11.5
    github.com/segmentio/kafka-go v0.4.47
    github.com/google/uuid v1.6.0
)
"""
        (path / "go.mod").write_text(go_mod)

        # Create Dockerfile for Go
        dockerfile = """FROM golang:1.21-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache gcc musl-dev

COPY go.mod go.sum* ./
RUN go mod download

COPY . .

RUN go build -o main .

CMD ["./main"]
"""
        (path / "Dockerfile").write_text(dockerfile)

    def _generate_c(self, service: ServiceBlock, path: Path):
        """Generate C/C++ service artifacts."""
        is_cpp = "cpp" in service.language or any(f.endswith(".hpp") for f in service.dependencies)
        
        ext = ".cpp" if is_cpp else ".c"
        (path / f"main{ext}").write_text(service.content)

        # Create CMakeLists.txt
        cmake = f"""cmake_minimum_required(VERSION 3.16)
project({service.name} {"CXX" if is_cpp else "C"})

set(CMAKE_{"CXX" if is_cpp else "C"}_STANDARD {"17" if is_cpp else "11"})

find_package(PkgConfig REQUIRED)
pkg_check_modules(HIREDIS REQUIRED hiredis)
pkg_check_modules(RDKAFKA REQUIRED rdkafka)
pkg_check_modules(CJSON REQUIRED libcjson)

add_executable({service.name} main{ext})

target_include_directories({service.name} PRIVATE 
    ${{HIREDIS_INCLUDE_DIRS}} 
    ${{RDKAFKA_INCLUDE_DIRS}}
    ${{CJSON_INCLUDE_DIRS}}
)

target_link_libraries({service.name} 
    ${{HIREDIS_LIBRARIES}} 
    ${{RDKAFKA_LIBRARIES}}
    ${{CJSON_LIBRARIES}}
    pthread
)
"""
        (path / "CMakeLists.txt").write_text(cmake)

        # Create Dockerfile for C/C++
        dockerfile = f"""FROM alpine:3.19

WORKDIR /app

# Install build tools and dependencies
RUN apk add --no-cache \\
    build-base \\
    cmake \\
    pkgconfig \\
    hiredis-dev \\
    librdkafka-dev \\
    cjson-dev

COPY . .

RUN mkdir build && cd build && \\
    cmake .. && \\
    make

CMD ["./build/{service.name}"]
"""
        (path / "Dockerfile").write_text(dockerfile)

