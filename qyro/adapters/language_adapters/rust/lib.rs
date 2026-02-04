// src/adapters/language_adapters/rust/nexus_adapter/src/lib.rs
use rdkafka::{
    config::ClientConfig,
    consumer::{Consumer, StreamConsumer},
    message::Message,
    producer::{FutureProducer, FutureRecord},
    util::Timeout,
};
use redis::Commands;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::Duration;
use tokio::time::sleep;

#[derive(Debug, Clone)]
pub struct NexusConfig {
    pub kafka_bootstrap_servers: String,
    pub redis_url: String,
    pub module_name: String,
}

impl Default for NexusConfig {
    fn default() -> Self {
        Self {
            kafka_bootstrap_servers: "localhost:9092".to_string(),
            redis_url: "redis://127.0.0.1:6379".to_string(),
            module_name: "rust_module".to_string(),
        }
    }
}

#[derive(Serialize, Deserialize, Debug)]
pub struct State {
    #[serde(flatten)]
    pub data: HashMap<String, serde_json::Value>,
}

pub struct Nexus {
    config: NexusConfig,
    kafka_producer: Option<FutureProducer>,
    redis_client: Option<redis::Client>,
    state_cache: State,
}

impl Nexus {
    pub fn new() -> Self {
        Self {
            config: NexusConfig::default(),
            kafka_producer: None,
            redis_client: None,
            state_cache: State {
                data: HashMap::new(),
            },
        }
    }

    pub fn with_config(config: NexusConfig) -> Self {
        Self {
            config,
            kafka_producer: None,
            redis_client: None,
            state_cache: State {
                data: HashMap::new(),
            },
        }
    }

    pub async fn connect(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Initialize Kafka producer
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", &self.config.kafka_bootstrap_servers)
            .set("message.timeout.ms", "5000")
            .create()
            .expect("Producer creation error");

        self.kafka_producer = Some(producer);

        // Initialize Redis client
        let redis_client = redis::Client::open(&*self.config.redis_url)?;
        self.redis_client = Some(redis_client);

        // Register module
        self.register_module().await?;

        Ok(())
    }

    async fn register_module(&self) -> Result<(), Box<dyn std::error::Error>> {
        if let Some(ref producer) = self.kafka_producer {
            let registration = serde_json::json!({
                "type": "module_registration",
                "module_name": &self.config.module_name,
                "timestamp": chrono::Utc::now().to_rfc3339(),
                "language": "rust"
            });

            let record = FutureRecord::to("nexus_module_events")
                .payload(&serde_json::to_string(&registration)?)
                .key(&self.config.module_name);

            producer.send(record, Timeout::After(Duration::from_secs(1))).await?;
        }
        Ok(())
    }

    pub async fn read_state(&mut self) -> Result<State, Box<dyn std::error::Error>> {
        if let Some(ref client) = self.redis_client {
            let mut conn = client.get_async_connection().await?;
            
            // Get all keys from Redis hash
            let result: Vec<(String, String)> = conn.hgetall("nexus:state").await?;
            
            let mut state_data = HashMap::new();
            for (key, value) in result {
                match serde_json::from_str::<serde_json::Value>(&value) {
                    Ok(parsed_value) => { state_data.insert(key, parsed_value); },
                    Err(_) => { state_data.insert(key, serde_json::Value::String(value)); },
                }
            }
            
            self.state_cache.data = state_data.clone();
            Ok(State { data: state_data })
        } else {
            Ok(self.state_cache.clone())
        }
    }

    pub async fn write_state(&self, state: &State) -> Result<(), Box<dyn std::error::Error>> {
        if let Some(ref client) = self.redis_client {
            let mut conn = client.get_async_connection().await?;
            
            // Update Redis hash with new state
            for (key, value) in &state.data {
                let value_str = serde_json::to_string(value)?;
                conn.hset("nexus:state", key, value_str).await?;
            }
            
            // Publish state change event to Kafka
            if let Some(ref producer) = self.kafka_producer {
                let state_change = serde_json::json!({
                    "type": "state_change",
                    "module": &self.config.module_name,
                    "changes": state.data,
                    "timestamp": chrono::Utc::now().to_rfc3339()
                });

                let record = FutureRecord::to("nexus_state_changes")
                    .payload(&serde_json::to_string(&state_change)?)
                    .key(&self.config.module_name);

                producer.send(record, Timeout::After(Duration::from_secs(1))).await?;
            }
        }
        Ok(())
    }

    pub async fn update_field(&self, key: &str, value: serde_json::Value) -> Result<(), Box<dyn std::error::Error>> {
        if let Some(ref client) = self.redis_client {
            let mut conn = client.get_async_connection().await?;
            
            let value_str = serde_json::to_string(&value)?;
            conn.hset("nexus:state", key, value_str).await?;
            
            // Publish field update event to Kafka
            if let Some(ref producer) = self.kafka_producer {
                let field_update = serde_json::json!({
                    "type": "field_update",
                    "module": &self.config.module_name,
                    "key": key,
                    "value": value,
                    "timestamp": chrono::Utc::now().to_rfc3339()
                });

                let record = FutureRecord::to("nexus_field_updates")
                    .payload(&serde_json::to_string(&field_update)?)
                    .key(key);

                producer.send(record, Timeout::After(Duration::from_secs(1))).await?;
            }
        }
        Ok(())
    }

    pub async fn subscribe_to_changes<F>(&self, mut callback: F) -> Result<(), Box<dyn std::error::Error>>
    where
        F: FnMut(State) + Send + 'static,
    {
        if let Some(ref producer) = self.kafka_producer {
            // This would typically run in a separate task
            // For simplicity, we'll just return Ok for now
            // In a real implementation, this would create a Kafka consumer
            println!("Subscribing to state changes...");
        }
        Ok(())
    }

    pub async fn call_remote_function(
        &self,
        func_name: &str,
        args: serde_json::Value,
    ) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        if let Some(ref producer) = self.kafka_producer {
            let request_id = uuid::Uuid::new_v4().to_string();
            let call_request = serde_json::json!({
                "type": "rpc_call",
                "request_id": request_id,
                "function": func_name,
                "args": args,
                "caller": &self.config.module_name,
                "timestamp": chrono::Utc::now().to_rfc3339()
            });

            let record = FutureRecord::to("nexus_rpc_requests")
                .payload(&serde_json::to_string(&call_request)?)
                .key(func_name);

            producer.send(record, Timeout::After(Duration::from_secs(1))).await?;
            
            // In a real implementation, we'd wait for the response
            // For now, return a placeholder
            Ok(serde_json::Value::String("response_pending".to_string()))
        } else {
            Ok(serde_json::Value::Null)
        }
    }

    pub async fn register_function(
        &self,
        func_name: &str,
        handler: impl Fn(serde_json::Value) -> serde_json::Value + Send + Sync + 'static,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Register function in a central registry
        if let Some(ref producer) = self.kafka_producer {
            let registration = serde_json::json!({
                "type": "function_registration",
                "function": func_name,
                "module": &self.config.module_name,
                "timestamp": chrono::Utc::now().to_rfc3339()
            });

            let record = FutureRecord::to("nexus_function_registry")
                .payload(&serde_json::to_string(&registration)?)
                .key(func_name);

            producer.send(record, Timeout::After(Duration::from_secs(1))).await?;
        }
        Ok(())
    }
}

// Helper functions for common operations
impl Nexus {
    pub async fn get_field(&mut self, key: &str) -> Result<Option<serde_json::Value>, Box<dyn std::error::Error>> {
        let state = self.read_state().await?;
        Ok(state.data.get(key).cloned())
    }

    pub async fn increment_field(&self, key: &str, amount: i64) -> Result<i64, Box<dyn std::error::Error>> {
        let current_value = self.get_field(key).await?;
        let current_num = match current_value {
            Some(serde_json::Value::Number(n)) => n.as_i64().unwrap_or(0),
            _ => 0,
        };
        
        let new_value = current_num + amount;
        self.update_field(key, serde_json::Value::Number(serde_json::Number::from(new_value))).await?;
        Ok(new_value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_nexus_creation() {
        let nexus = Nexus::new();
        assert_eq!(nexus.config.module_name, "rust_module");
    }
}