// src/adapters/language_adapters/rust/nexus_adapter/src/lib.rs
use rdkafka::{
    config::ClientConfig,
    producer::{FutureProducer, FutureRecord},
    util::Timeout,
};
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use std::env;
use std::time::Duration;
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Debug, Clone)]
pub struct QyroConfig {
    pub kafka_servers: String,
    pub redis_url: String,
    pub module_name: String,
}

impl Default for QyroConfig {
    fn default() -> Self {
        Self {
            kafka_servers: env::var("QYRO_KAFKA_BOOTSTRAP_SERVERS").unwrap_or_else(|_| "localhost:9092".to_string()),
            redis_url: format!(
                "redis://{}:{}/{}",
                env::var("QYRO_REDIS_HOST").unwrap_or_else(|_| "localhost".to_string()),
                env::var("QYRO_REDIS_PORT").unwrap_or_else(|_| "6379".to_string()),
                env::var("QYRO_REDIS_DB").unwrap_or_else(|_| "0".to_string())
            ),
            module_name: env::var("QYRO_MODULE_NAME").unwrap_or_else(|_| "rust_module".to_string()),
        }
    }
}

pub struct Qyro {
    config: QyroConfig,
    producer: Option<FutureProducer>,
    redis: Option<redis::Client>,
}

impl Qyro {
    pub async fn new() -> Self {
        let config = QyroConfig::default();
        let mut qyro = Self {
            config,
            producer: None,
            redis: None,
        };
        qyro.connect().await;
        qyro
    }

    async fn connect(&mut self) {
        // Redis
        match redis::Client::open(&*self.config.redis_url) {
            Ok(client) => self.redis = Some(client),
            Err(e) => eprintln!("[QYRO] Redis connection failed: {}", e),
        }

        // Kafka
        let producer: Result<FutureProducer, _> = ClientConfig::new()
            .set("bootstrap.servers", &self.config.kafka_servers)
            .create();
            
        match producer {
            Ok(p) => self.producer = Some(p),
            Err(e) => eprintln!("[QYRO] Kafka connection failed: {}", e),
        }
    }

    pub async fn get<T: for<'de> Deserialize<'de>>(&self, key: &str) -> Option<T> {
        if let Some(client) = &self.redis {
            if let Ok(mut conn) = client.get_async_connection().await {
                let val: Option<String> = conn.get(key).await.ok()?;
                if let Some(v) = val {
                    return serde_json::from_str(&v).ok();
                }
            }
        }
        None
    }

    pub async fn set<T: Serialize>(&self, key: &str, value: &T) {
        if let Some(client) = &self.redis {
            if let Ok(mut conn) = client.get_async_connection().await {
                if let Ok(json) = serde_json::to_string(value) {
                    let _: Result<(), _> = conn.set(key, json).await;
                }
            }
        }
    }

    pub async fn emit<T: Serialize>(&self, topic: &str, data: &T) {
        if let Some(producer) = &self.producer {
            if let Ok(json) = serde_json::to_string(data) {
                let _ = producer.send(
                    FutureRecord::to(topic).payload(&json).key(&self.config.module_name),
                    Timeout::After(Duration::from_secs(1))
                ).await;
            }
        } else if let Some(client) = &self.redis {
            // Fallback to Redis PubSub
             if let Ok(mut conn) = client.get_async_connection().await {
                if let Ok(json) = serde_json::to_string(data) {
                    let _: Result<(), _> = conn.publish(format!("qyro:{}", topic), json).await;
                }
            }
        }
    }
}
