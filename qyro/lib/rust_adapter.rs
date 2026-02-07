//! Qyro Rust Adapter v2 - Enhanced with RPC Support
//!
//! Provides the Qyro API for Rust services:
//! - Shared state (Redis)
//! - Event streaming (Kafka)
//! - Cross-language RPC
//!
//! For detailed usage examples, visit: https://qyro.dev/docs/rust-adapter

use redis::Commands;
use rdkafka::config::ClientConfig;
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::consumer::{StreamConsumer, Consumer, CommitMode};
use rdkafka::message::{Message, OwnedMessage};
use serde::{Serialize, Deserialize};
use serde_json::{Value, json};
use std::env;
use std::collections::HashMap;
use std::sync::{Arc, Mutex, RwLock};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::sync::oneshot;
use uuid::Uuid;
use lazy_static::lazy_static;

// =============================================================================
// Configuration
// =============================================================================

lazy_static! {
    static ref REDIS_HOST: String = env::var("REDIS_HOST").unwrap_or_else(|_| "redis".to_string());
    static ref REDIS_PORT: String = env::var("REDIS_PORT").unwrap_or_else(|_| "6379".to_string());
    static ref KAFKA_SERVERS: String = env::var("KAFKA_BOOTSTRAP_SERVERS").unwrap_or_else(|_| "kafka:9092".to_string());
    static ref SERVICE_NAME: String = env::var("QYRO_SERVICE_NAME").unwrap_or_else(|_| "rust-service".to_string());
    static ref RPC_TIMEOUT: u64 = env::var("QYRO_RPC_TIMEOUT")
        .unwrap_or_else(|_| "30".to_string())
        .parse()
        .unwrap_or(30);
}

const RPC_TOPIC: &str = "qyro.rpc.requests";
const RPC_RESPONSE_TOPIC: &str = "qyro.rpc.responses";

// =============================================================================
// RPC Types
// =============================================================================

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RPCRequest {
    pub request_id: String,
    pub source_service: String,
    pub target_service: String,
    pub function_name: String,
    pub args: Vec<Value>,
    pub kwargs: HashMap<String, Value>,
    pub timestamp: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RPCResponse {
    pub request_id: String,
    pub source_service: String,
    pub success: bool,
    pub result: Option<Value>,
    pub error: Option<String>,
    pub timestamp: f64,
}

// =============================================================================
// Function Registry
// =============================================================================

type BoxedFunction = Box<dyn Fn(Vec<Value>) -> Result<Value, String> + Send + Sync>;

lazy_static! {
    static ref EXPOSED_FUNCTIONS: RwLock<HashMap<String, Arc<BoxedFunction>>> = 
        RwLock::new(HashMap::new());
    static ref PENDING_REQUESTS: Mutex<HashMap<String, oneshot::Sender<Result<Value, String>>>> = 
        Mutex::new(HashMap::new());
}

/// Metadata for an exposed function
#[derive(Debug, Clone, Serialize)]
pub struct FunctionMeta {
    pub name: String,
    pub full_name: String,
    pub service: String,
}

// =============================================================================
// Main Qyro Struct
// =============================================================================

pub struct Qyro;

impl Qyro {
    // =========================================================================
    // Connection Helpers
    // =========================================================================

    fn get_redis_url() -> String {
        format!("redis://{}:{}", *REDIS_HOST, *REDIS_PORT)
    }

    fn get_redis_client() -> redis::RedisResult<redis::Client> {
        redis::Client::open(Self::get_redis_url())
    }

    fn create_producer() -> FutureProducer {
        ClientConfig::new()
            .set("bootstrap.servers", &*KAFKA_SERVERS)
            .set("message.timeout.ms", "5000")
            .create()
            .expect("Failed to create Kafka producer")
    }

    // =========================================================================
    // Shared State API (Redis)
    // =========================================================================

    /// Set a value in shared memory (Redis).
    pub fn set<T: Serialize>(key: &str, value: &T) -> redis::RedisResult<()> {
        let client = Self::get_redis_client()?;
        let mut con = client.get_connection()?;
        let val_str = serde_json::to_string(value).unwrap();
        con.set(key, val_str)
    }

    /// Get a value from shared memory (Redis).
    pub fn get(key: &str) -> redis::RedisResult<Option<String>> {
        let client = Self::get_redis_client()?;
        let mut con = client.get_connection()?;
        con.get(key)
    }

    /// Get a value and deserialize it.
    pub fn get_json<T: for<'de> Deserialize<'de>>(key: &str) -> Option<T> {
        match Self::get(key) {
            Ok(Some(val)) => serde_json::from_str(&val).ok(),
            _ => None,
        }
    }

    /// Delete a key from shared memory.
    pub fn delete(key: &str) -> redis::RedisResult<bool> {
        let client = Self::get_redis_client()?;
        let mut con = client.get_connection()?;
        let deleted: i32 = con.del(key)?;
        Ok(deleted > 0)
    }

    /// Check if a key exists.
    pub fn exists(key: &str) -> redis::RedisResult<bool> {
        let client = Self::get_redis_client()?;
        let mut con = client.get_connection()?;
        con.exists(key)
    }

    /// Increment a counter.
    pub fn incr(key: &str, amount: i64) -> redis::RedisResult<i64> {
        let client = Self::get_redis_client()?;
        let mut con = client.get_connection()?;
        con.incr(key, amount)
    }

    /// Set expiration on a key.
    pub fn expire(key: &str, seconds: usize) -> redis::RedisResult<bool> {
        let client = Self::get_redis_client()?;
        let mut con = client.get_connection()?;
        con.expire(key, seconds as i64)
    }

    // =========================================================================
    // Event Streaming API (Kafka)
    // =========================================================================

    /// Publish a message to a topic.
    pub async fn publish<T: Serialize>(topic: &str, message: &T) {
        let producer = Self::create_producer();
        let payload = serde_json::to_string(message).unwrap();

        producer
            .send(
                FutureRecord::to(topic)
                    .payload(&payload)
                    .key("key"),
                Duration::from_secs(5),
            )
            .await
            .expect("Failed to send message");
    }

    /// Create a Kafka consumer for subscribing.
    pub fn create_consumer(topic: &str, group_id: Option<&str>) -> StreamConsumer {
        let default_gid = format!("qyro-{}", *SERVICE_NAME);
        let gid = group_id.unwrap_or(&default_gid);
        
        let consumer: StreamConsumer = ClientConfig::new()
            .set("bootstrap.servers", &*KAFKA_SERVERS)
            .set("group.id", gid)
            .set("enable.auto.commit", "true")
            .set("auto.offset.reset", "earliest")
            .create()
            .expect("Failed to create consumer");

        consumer
            .subscribe(&[topic])
            .expect("Failed to subscribe to topic");

        consumer
    }

    // =========================================================================
    // Cross-Language RPC API
    // =========================================================================

    /// Expose a function for RPC calls.
    /// 
    /// # Example
    /// ```
    /// Qyro::expose("calculate", |args| {
    ///     let a = args[0].as_i64().unwrap_or(0);
    ///     let b = args[1].as_i64().unwrap_or(0);
    ///     Ok(json!(a + b))
    /// });
    /// ```
    pub fn expose<F>(name: &str, f: F)
    where
        F: Fn(Vec<Value>) -> Result<Value, String> + Send + Sync + 'static,
    {
        let full_name = format!("{}.{}", *SERVICE_NAME, name);
        let mut functions = EXPOSED_FUNCTIONS.write().unwrap();
        functions.insert(full_name.clone(), Arc::new(Box::new(f)));
        Self::info(&format!("Exposed function: {}", full_name));
    }

    /// Call a function in another service.
    /// 
    /// # Example
    /// ```
    /// let result = Qyro::call("api.calculate", vec![json!(1), json!(2)]).await?;
    /// ```
    pub async fn call(function_path: &str, args: Vec<Value>) -> Result<Value, String> {
        let parts: Vec<&str> = function_path.splitn(2, '.').collect();
        if parts.len() != 2 {
            return Err(format!("Invalid function path: {}", function_path));
        }

        let target_service = parts[0];
        let request_id = Uuid::new_v4().to_string();

        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs_f64();

        let request = RPCRequest {
            request_id: request_id.clone(),
            source_service: SERVICE_NAME.clone(),
            target_service: target_service.to_string(),
            function_name: function_path.to_string(),
            args,
            kwargs: HashMap::new(),
            timestamp,
        };

        // Create oneshot channel for response
        let (tx, rx) = oneshot::channel();
        {
            let mut pending = PENDING_REQUESTS.lock().unwrap();
            pending.insert(request_id.clone(), tx);
        }

        // Send request
        Self::publish(RPC_TOPIC, &request).await;

        // Wait for response with timeout
        match tokio::time::timeout(Duration::from_secs(*RPC_TIMEOUT), rx).await {
            Ok(Ok(result)) => result,
            Ok(Err(_)) => Err("Response channel closed".to_string()),
            Err(_) => {
                // Clean up pending request
                let mut pending = PENDING_REQUESTS.lock().unwrap();
                pending.remove(&request_id);
                Err(format!(
                    "RPC call to '{}' timed out after {}s",
                    function_path, *RPC_TIMEOUT
                ))
            }
        }
    }

    /// Start the RPC server in the background.
    pub async fn start_rpc_server() {
        let consumer = Self::create_consumer(RPC_TOPIC, Some(&format!("qyro-rpc-server-{}", *SERVICE_NAME)));
        let producer = Self::create_producer();

        Self::info(&format!("RPC Server started for service: {}", *SERVICE_NAME));

        tokio::spawn(async move {
            use rdkafka::message::BorrowedMessage;
            use futures::StreamExt;

            let stream = consumer.stream();
            futures::pin_mut!(stream);

            while let Some(result) = stream.next().await {
                match result {
                    Ok(message) => {
                        if let Some(payload) = message.payload() {
                            if let Ok(request) = serde_json::from_slice::<RPCRequest>(payload) {
                                // Check if this request is for us
                                if request.target_service != *SERVICE_NAME {
                                    continue;
                                }

                                let response = Self::handle_rpc_request(&request);

                                // Send response
                                let response_json = serde_json::to_string(&response).unwrap();
                                let _ = producer
                                    .send(
                                        FutureRecord::to(RPC_RESPONSE_TOPIC)
                                            .payload(&response_json)
                                            .key("key"),
                                        Duration::from_secs(5),
                                    )
                                    .await;
                            }
                        }
                        let _ = consumer.commit_message(&message, CommitMode::Async);
                    }
                    Err(e) => {
                        Self::error(&format!("Kafka error: {}", e));
                    }
                }
            }
        });
    }

    fn handle_rpc_request(request: &RPCRequest) -> RPCResponse {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs_f64();

        let functions = EXPOSED_FUNCTIONS.read().unwrap();
        
        match functions.get(&request.function_name) {
            Some(func) => {
                match func(request.args.clone()) {
                    Ok(result) => RPCResponse {
                        request_id: request.request_id.clone(),
                        source_service: SERVICE_NAME.clone(),
                        success: true,
                        result: Some(result),
                        error: None,
                        timestamp,
                    },
                    Err(e) => RPCResponse {
                        request_id: request.request_id.clone(),
                        source_service: SERVICE_NAME.clone(),
                        success: false,
                        result: None,
                        error: Some(e),
                        timestamp,
                    },
                }
            }
            None => RPCResponse {
                request_id: request.request_id.clone(),
                source_service: SERVICE_NAME.clone(),
                success: false,
                result: None,
                error: Some(format!("Function '{}' not found", request.function_name)),
                timestamp,
            },
        }
    }

    /// Start listening for RPC responses.
    pub async fn start_response_listener() {
        let consumer = Self::create_consumer(
            RPC_RESPONSE_TOPIC,
            Some(&format!("qyro-rpc-client-{}-{}", *SERVICE_NAME, Uuid::new_v4())),
        );

        tokio::spawn(async move {
            use futures::StreamExt;

            let stream = consumer.stream();
            futures::pin_mut!(stream);

            while let Some(result) = stream.next().await {
                if let Ok(message) = result {
                    if let Some(payload) = message.payload() {
                        if let Ok(response) = serde_json::from_slice::<RPCResponse>(payload) {
                            let mut pending = PENDING_REQUESTS.lock().unwrap();
                            if let Some(tx) = pending.remove(&response.request_id) {
                                let result = if response.success {
                                    Ok(response.result.unwrap_or(Value::Null))
                                } else {
                                    Err(response.error.unwrap_or_else(|| "Unknown error".to_string()))
                                };
                                let _ = tx.send(result);
                            }
                        }
                    }
                    let _ = consumer.commit_message(&message, CommitMode::Async);
                }
            }
        });
    }

    /// List all exposed functions.
    pub fn list_exposed_functions() -> Vec<FunctionMeta> {
        let functions = EXPOSED_FUNCTIONS.read().unwrap();
        functions
            .keys()
            .map(|full_name| {
                let parts: Vec<&str> = full_name.splitn(2, '.').collect();
                FunctionMeta {
                    name: parts.get(1).unwrap_or(&"").to_string(),
                    full_name: full_name.clone(),
                    service: SERVICE_NAME.clone(),
                }
            })
            .collect()
    }

    // =========================================================================
    // Service Discovery
    // =========================================================================

    /// Register this service for discovery.
    pub fn register_service(metadata: Option<HashMap<String, Value>>) {
        let functions = Self::list_exposed_functions();
        let mut service_info = json!({
            "name": *SERVICE_NAME,
            "host": env::var("HOSTNAME").unwrap_or_else(|_| "localhost".to_string()),
            "functions": functions,
        });

        if let Some(meta) = metadata {
            if let Value::Object(ref mut obj) = service_info {
                for (k, v) in meta {
                    obj.insert(k, v);
                }
            }
        }

        let key = format!("qyro:service:{}", *SERVICE_NAME);
        let _ = Self::set(&key, &service_info);
        Self::info(&format!("Service registered: {}", *SERVICE_NAME));
    }

    // =========================================================================
    // Logging
    // =========================================================================

    pub fn log(message: &str, level: &str) {
        let timestamp = chrono::Utc::now().to_rfc3339();
        println!("[{}] [{}] [{}] {}", timestamp, level, *SERVICE_NAME, message);
    }

    pub fn info(message: &str) { Self::log(message, "INFO"); }
    pub fn warn(message: &str) { Self::log(message, "WARN"); }
    pub fn error(message: &str) { Self::log(message, "ERROR"); }
    pub fn debug(message: &str) { Self::log(message, "DEBUG"); }
}

// =============================================================================
// Macro for easy function exposure
// =============================================================================

/// Macro to easily expose functions with proper type conversion.
/// 
/// # Example
/// ```
/// qyro_expose!(calculate, |a: i64, b: i64| -> i64 {
///     a + b
/// });
/// ```
#[macro_export]
macro_rules! qyro_expose {
    ($name:ident, $closure:expr) => {
        Qyro::expose(stringify!($name), |args| {
            let result = $closure;
            Ok(serde_json::to_value(result).unwrap())
        });
    };
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rpc_request_serialization() {
        let request = RPCRequest {
            request_id: "test-123".to_string(),
            source_service: "test-service".to_string(),
            target_service: "api".to_string(),
            function_name: "api.calculate".to_string(),
            args: vec![json!(1), json!(2)],
            kwargs: HashMap::new(),
            timestamp: 1234567890.0,
        };

        let json = serde_json::to_string(&request).unwrap();
        let parsed: RPCRequest = serde_json::from_str(&json).unwrap();
        
        assert_eq!(parsed.request_id, "test-123");
        assert_eq!(parsed.function_name, "api.calculate");
    }
}
