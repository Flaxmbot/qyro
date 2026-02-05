#!/usr/bin/env python3
"""
Qyro Gateway entry point for Docker.

This module reads configuration from environment variables.
"""

import os
import sys
from pathlib import Path

# Add qyro to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from qyro.gateway import QyroGateway

def main():
    """Main entry point for the gateway."""
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    kafka_bootstrap_servers = os.getenv("QYRO_KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    
    gateway = QyroGateway(
        host=host,
        port=port,
        kafka_bootstrap_servers=kafka_bootstrap_servers
    )
    
    gateway.start()

if __name__ == '__main__':
    main()
