import os
import yaml
from pathlib import Path
from typing import Dict, List, Any

class QyroK8sBuilder:
    def __init__(self, qyro_file: str, output_dir: str = "qyro_k8s"):
        self.qyro_file = qyro_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.project_name = Path(qyro_file).stem.lower().replace("_", "-")

    def build(self, named_blocks: Dict[str, List[Dict[str, Any]]]):
        print(f"[QYRO] Generating Kubernetes manifests in {self.output_dir}...")

        # 1. ConfigMap (Environment Variables)
        self._generate_configmap()

        # 2. Redis & Kafka (Stateful Sets / Deployments)
        self._generate_infrastructure()

        # 3. Application Deployment
        self._generate_app_deployment()

        # 4. Service
        self._generate_service()

        # 5. Kustomization (for easy apply)
        self._generate_kustomization()

        print(f"[QYRO] K8s manifests generated. Apply with: kubectl apply -k {self.output_dir}")

    def _generate_configmap(self):
        config = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": f"{self.project_name}-config"},
            "data": {
                "QYRO_REDIS_HOST": f"{self.project_name}-redis",
                "QYRO_REDIS_PORT": "6379",
                "QYRO_KAFKA_BOOTSTRAP_SERVERS": f"{self.project_name}-kafka:9092"
            }
        }
        with open(self.output_dir / "configmap.yaml", "w") as f:
            yaml.dump(config, f)

    def _generate_infrastructure(self):
        # Redis
        redis = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": f"{self.project_name}-redis"},
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": f"{self.project_name}-redis"}},
                "template": {
                    "metadata": {"labels": {"app": f"{self.project_name}-redis"}},
                    "spec": {
                        "containers": [{
                            "name": "redis",
                            "image": "redis:7-alpine",
                            "ports": [{"containerPort": 6379}]
                        }]
                    }
                }
            }
        }
        redis_svc = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": f"{self.project_name}-redis"},
            "spec": {
                "selector": {"app": f"{self.project_name}-redis"},
                "ports": [{"port": 6379, "targetPort": 6379}]
            }
        }

        # Kafka (Simplified for demo - usually use Helm/Operator)
        kafka = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": f"{self.project_name}-kafka"},
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": f"{self.project_name}-kafka"}},
                "template": {
                    "metadata": {"labels": {"app": f"{self.project_name}-kafka"}},
                    "spec": {
                        "containers": [
                            {
                                "name": "kafka",
                                "image": "confluentinc/cp-kafka:latest",
                                "env": [
                                    {"name": "KAFKA_NODE_ID", "value": "1"},
                                    {"name": "KAFKA_PROCESS_ROLES", "value": "broker,controller"},
                                    {"name": "KAFKA_LISTENERS", "value": "PLAINTEXT://:9092,CONTROLLER://:9093"},
                                    {"name": "KAFKA_ADVERTISED_LISTENERS", "value": f"PLAINTEXT://{self.project_name}-kafka:9092"},
                                    {"name": "KAFKA_CONTROLLER_LISTENER_NAMES", "value": "CONTROLLER"},
                                    {"name": "KAFKA_CONTROLLER_QUORUM_VOTERS", "value": "1@localhost:9093"},
                                    {"name": "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR", "value": "1"},
                                    {"name": "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR", "value": "1"},
                                    {"name": "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR", "value": "1"},
                                    {"name": "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS", "value": "0"},
                                    {"name": "KAFKA_NUM_PARTITIONS", "value": "1"}
                                ],
                                "ports": [{"containerPort": 9092}]
                            }
                        ]
                    }
                }
            }
        }
        kafka_svc = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": f"{self.project_name}-kafka"},
            "spec": {
                "selector": {"app": f"{self.project_name}-kafka"},
                "ports": [{"port": 9092, "targetPort": 9092}]
            }
        }

        with open(self.output_dir / "infrastructure.yaml", "w") as f:
            yaml.dump_all([redis, redis_svc, kafka, kafka_svc], f)

    def _generate_app_deployment(self):
        # We assume the Docker image is built and pushed as 'qyro-app:latest'
        # In real world, user provides image registry
        deploy = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": f"{self.project_name}-app"},
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": f"{self.project_name}-app"}},
                "template": {
                    "metadata": {"labels": {"app": f"{self.project_name}-app"}},
                    "spec": {
                        "containers": [{
                            "name": "app",
                            "image": "qyro-app:latest", # Placeholder
                            "imagePullPolicy": "Never", # For local Minikube/Kind
                            "ports": [
                                {"containerPort": 8000},
                                {"containerPort": 8765}
                            ],
                            "envFrom": [
                                {"configMapRef": {"name": f"{self.project_name}-config"}}
                            ]
                        }]
                    }
                }
            }
        }
        with open(self.output_dir / "deployment.yaml", "w") as f:
            yaml.dump(deploy, f)

    def _generate_service(self):
        svc = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": f"{self.project_name}-gateway"},
            "spec": {
                "type": "NodePort", # Or LoadBalancer
                "selector": {"app": f"{self.project_name}-app"},
                "ports": [
                    {"name": "http", "port": 80, "targetPort": 8000},
                    {"name": "ws", "port": 8765, "targetPort": 8765}
                ]
            }
        }
        with open(self.output_dir / "service.yaml", "w") as f:
            yaml.dump(svc, f)

    def _generate_kustomization(self):
        kust = {
            "resources": [
                "configmap.yaml",
                "infrastructure.yaml",
                "deployment.yaml",
                "service.yaml"
            ]
        }
        with open(self.output_dir / "kustomization.yaml", "w") as f:
            yaml.dump(kust, f)
