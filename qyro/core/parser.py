import re
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
import qyro.lib

class ServiceBlock(BaseModel):
    language: str
    name: str
    dependencies: List[str]
    content: str
    start_line: int

class QyroParser:
    BLOCK_REGEX = re.compile(r"^>>>(?P<lang>\w+):(?P<name>[\w-]+)(?:\s*\[(?P<deps>.*)\])?")

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.content = self.filepath.read_text()
        self.services: List[ServiceBlock] = []

    def parse(self):
        lines = self.content.splitlines()
        current_block: Optional[ServiceBlock] = None
        buffer = []

        for i, line in enumerate(lines):
            match = self.BLOCK_REGEX.match(line)
            if match:
                if current_block:
                    current_block.content = "\n".join(buffer).strip()
                    self.services.append(current_block)
                    buffer = []

                lang = match.group("lang")
                name = match.group("name")
                deps_str = match.group("deps")
                deps = [d.strip() for d in deps_str.split(",")] if deps_str else []

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

        self._copy_adapters(path)

        from qyro.core.templates import DOCKERFILE_PYTHON
        (path / "Dockerfile").write_text(DOCKERFILE_PYTHON.format(filename="main.py"))

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

        self._copy_adapters(path)

        from qyro.core.templates import DOCKERFILE_NODE
        (path / "Dockerfile").write_text(DOCKERFILE_NODE)

    def _generate_rust(self, service: ServiceBlock, path: Path):
        deps_lines = ""
        user_deps = set(service.dependencies)
        # Add defaults
        defaults = {
            "redis": "0.23",
            "rdkafka": "0.29",
            "serde": '{ version = "1.0", features = ["derive"] }',
            "serde_json": "1.0",
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

        self._copy_adapters(path)

        from qyro.core.templates import DOCKERFILE_RUST
        (path / "Dockerfile").write_text(DOCKERFILE_RUST.format(bin_name=service.name))

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
                                    <mainClass>Main</mainClass>
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

        src_path = path / "src" / "main" / "java"
        src_path.mkdir(parents=True, exist_ok=True)
        (src_path / "Main.java").write_text(service.content)

        # We need to also put Qyro.java there.
        # copy adapters first
        self._copy_adapters(path)
        # Move Qyro.java to src path
        adapter_dest = src_path / "com" / "qyro" / "adapters"
        adapter_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(path / "qyro_adapters" / "java_adapter.java", adapter_dest / "Qyro.java")

        from qyro.core.templates import DOCKERFILE_JAVA
        (path / "Dockerfile").write_text(DOCKERFILE_JAVA)

    def _get_docker_config(self, service: ServiceBlock, type: str):
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
            config += """
    ports:
      - "3000-3010:3000"
    stdin_open: true
    tty: true
"""
        elif type == "python":
            # Heuristic: expose 8000 if it looks like a web service
            if any(d in service.dependencies for d in ["fastapi", "flask", "django", "uvicorn"]):
                config += """
    ports:
      - "8000-8010:8000"
"""
        return config
