#!/usr/bin/env python3
"""
Qyro Orchestrator entry point for Docker.

This module reads the QYRO_FILE and QYRO_FILE_DIR environment variables
to locate and run the Qyro application.
"""

import os
import sys
from pathlib import Path

# Get environment variables
qyro_file_name = os.environ.get('QYRO_FILE', 'app.qyro')
qyro_file_dir = os.environ.get('QYRO_FILE_DIR', '/app')

# Construct the full path to the qyro file
qyro_file_path = Path(qyro_file_dir) / qyro_file_name

if not qyro_file_path.exists():
    print(f"Error: Qyro file not found at {qyro_file_path}", file=sys.stderr)
    sys.exit(1)

# Add qyro to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from qyro.orchestrator import QyroOrchestrator
from qyro.common.config import QyroConfig
from qyro.common.kafka_manager import KafkaManager

def main():
    """Main entry point for the orchestrator."""
    # Load configuration from environment or use defaults
    config = QyroConfig(
        redis_host=os.environ.get('REDIS_HOST', 'localhost'),
        redis_port=int(os.environ.get('REDIS_PORT', 6379)),
        redis_password=os.environ.get('REDIS_PASSWORD'),
        kafka_bootstrap_servers=os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        debug=os.environ.get('DEBUG', 'false').lower() == 'true'
    )
    
    # Create and start the orchestrator
    orchestrator = QyroOrchestrator(
        qyro_file=str(qyro_file_path),
        config=config,
        skip_missing=True
    )
    
    orchestrator.start()

if __name__ == '__main__':
    main()
