"""
Qyro Gateway Service
Provides a REST and WebSocket API for interacting with Qyro modules.
"""

import asyncio
import asyncio
import json
import time
from typing import Dict, Any, Optional
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid

from qyro.common.kafka_manager import KafkaManager
from qyro.common.config import QyroConfig
from qyro.common.logging import get_logger


logger = get_logger("Qyro.gateway")


class QyroGateway:
    """REST and WebSocket gateway for Qyro applications."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765, kafka_bootstrap_servers: str = "localhost:9092"):
        self.host = host
        self.port = port
        self.app = FastAPI(title="Qyro Gateway", version="2.0.0")
        
        # Initialize configuration
        self.config = QyroConfig(
            service_host=host,
            service_port=port,
            kafka_bootstrap_servers=kafka_bootstrap_servers
        )
        
        # Initialize Kafka manager
        # Initialize Kafka manager
        self.kafka_manager = None
        try:
            self.kafka_manager = KafkaManager(self.config)
        except Exception:
            logger.warning("Kafka setup failed, will try Redis fallback")

        # Initialize Redis Memory
        from qyro.common.redis_memory import RedisQyroMemory
        self.redis_memory = None
        try:
            self.redis_memory = RedisQyroMemory(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password
            )
            logger.info("Gateway connected to Redis")
        except Exception as e:
            logger.error(f"Gateway failed to connect to Redis: {e}")

        if not self.kafka_manager and not self.redis_memory:
            logger.warning("Gateway running without ANY messaging backend!")

        # Start background listeners
        import threading
        self._listener_thread = threading.Thread(target=self._run_background_listeners, daemon=True)
        self._listener_thread.start()
        
        # WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Setup FastAPI routes and middleware
        self._setup_routes()
        self._setup_middleware()
        
        logger.info(f"Qyro Gateway initialized on {host}:{port}")

    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, configure specific origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup FastAPI routes."""
        @self.app.get("/")
        async def root():
            return {"message": "Qyro Gateway v2.0.0", "status": "running"}
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "service": "Qyro-gateway"}
        
        @self.app.get("/ready")
        async def ready():
            # Check if Kafka is available
            kafka_ready = self.kafka_manager.producer is not None
            return {"status": "ready", "kafka_connected": kafka_ready}
        
        @self.app.get("/state")
        async def get_state():
            """Get the current application state."""
            # This would typically fetch from Redis, but we'll use Kafka to broadcast a request
            # and wait for responses from modules
            try:
                request_id = str(uuid.uuid4())
                await self.kafka_manager.send_message(
                    topic=f"{self.config.kafka_topic_prefix}state_request",
                    message={"request_id": request_id, "action": "get_state"},
                    key=request_id
                )
                
                # In a real implementation, we'd wait for responses here
                # For now, return a placeholder
                return {"state": "placeholder", "request_id": request_id}
            except Exception as e:
                logger.error(f"Error getting state: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/state")
        async def update_state(state: Dict[str, Any]):
            """Update the application state."""
            try:
                await self.kafka_manager.publish_state_change(state, "gateway")
                return {"status": "success", "updated_keys": list(state.keys())}
            except Exception as e:
                logger.error(f"Error updating state: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            client_id = str(uuid.uuid4())
            self.active_connections[client_id] = websocket
            logger.info(f"WebSocket client connected: {client_id}")
            
            try:
                # Subscribe to Kafka state changes and forward to WebSocket
                async def kafka_state_handler(state_diff):
                    if client_id in self.active_connections:
                        try:
                            await self.active_connections[client_id].send_text(json.dumps({
                                "type": "state_update",
                                "data": state_diff,
                                "timestamp": time.time()
                            }))
                        except Exception as e:
                            logger.error(f"Error sending to WebSocket: {e}")
                
                # Start listening for state changes
                if self.kafka_manager:
                    await self.kafka_manager.subscribe_to_state_changes(kafka_state_handler)
                
                # Handle incoming WebSocket messages
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Forward WebSocket messages to Kafka/Redis
                    if message.get("type") == "rpc_call":
                        request_id = str(uuid.uuid4())
                        if self.kafka_manager:
                            await self.kafka_manager.publish_rpc_request(
                                message.get("function", ""),
                                message.get("args", {}),
                                request_id
                            )
                        elif self.redis_memory:
                            # Simple Redis fallback for RPC (event publish)
                            event_data = {
                                "id": request_id,
                                "fn": message.get("function", ""),
                                "args": message.get("args", {}),
                                "caller": f"websocket_{client_id}"
                            }
                            # Publish to generic events channel which Python adapter listens to
                            # Python adapter expects: {"type": "function_call", "data": ...}
                            # But PythonAdapter.publish_event wraps it.
                            # We need to match PythonAdapter._dispatch_message logic.
                            # It listens to `Qyro:events`.
                            # Payload: {"type": "function_call", ...}
                            full_event = {
                                "type": "function_call",
                                "module": "gateway",
                                "pid": "gateway",
                                "timestamp": time.time(),
                                "data": event_data
                            }
                            self.redis_memory.publish_event(full_event)

                    elif message.get("type") == "state_update":
                        if self.kafka_manager:
                            await self.kafka_manager.publish_state_change(
                                message.get("data", {}),
                                f"websocket_{client_id}"
                            )
                        elif self.redis_memory:
                            self.redis_memory.write(message.get("data", {}))
                        
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {client_id}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                if client_id in self.active_connections:
                    del self.active_connections[client_id]

    def _run_background_listeners(self):
        """Run background listeners for Redis/Kafka."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def listeners():
            if self.kafka_manager:
                try:
                    await self.kafka_manager.start_producer()
                    asyncio.create_task(self.start_kafka_listeners())
                except Exception as e:
                    logger.error(f"Kafka startup failed: {e}")
                    self.kafka_manager = None

            if self.redis_memory and not self.kafka_manager:
                logger.info("Using Redis listener fallback")
                # Redis subscribes in a blocking way usually, so we need careful handling or just rely on the memory class
                # The RedisQyroMemory class has subscribe_to_changes which uses a thread.
                # We can reuse that.
                self.redis_memory.subscribe_to_changes(self._handle_redis_state_change)

        loop.run_until_complete(listeners())
        loop.run_forever()

    def _handle_redis_state_change(self, state):
        """Handle state change from Redis."""
        # Broadcast to WebSockets
        asyncio.run_coroutine_threadsafe(self._broadcast_state_to_websockets(state), asyncio.get_event_loop())

    async def _broadcast_state_to_websockets(self, state):
        """Broadcast state to all connected clients."""
        message = json.dumps({
            "type": "state_update",
            "data": state,
            "timestamp": time.time()
        })
        disconnected = []
        for client_id, ws in self.active_connections.items():
            try:
                await ws.send_text(message)
            except:
                disconnected.append(client_id)
        for client_id in disconnected:
             del self.active_connections[client_id]

    async def start_kafka_listeners(self):
        """Start Kafka listeners for gateway functionality."""
        # Listen for module events
        async def module_event_handler(event):
            # Broadcast module events to all WebSocket connections
            message = {
                "type": "module_event",
                "data": event,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            disconnected_clients = []
            for client_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception:
                    disconnected_clients.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                if client_id in self.active_connections:
                    del self.active_connections[client_id]

        # Subscribe to module events
        try:
            if self.kafka_manager:
                await self.kafka_manager.consume_messages(
                    f"{self.config.kafka_topic_prefix}module_events",
                    module_event_handler
                )
        except Exception as e:
            logger.error(f"Error starting Kafka listeners: {e}")

    def start(self):
        """Start the Qyro gateway service."""
        logger.info(f"Starting Qyro Gateway on {self.host}:{self.port}")
        
        # Start the FastAPI server
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info" if not self.config.debug else "debug"
        )
