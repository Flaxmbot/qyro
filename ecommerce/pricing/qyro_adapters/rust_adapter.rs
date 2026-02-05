use redis::Commands;
use rdkafka::config::ClientConfig;
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::consumer::{StreamConsumer, Consumer};
use rdkafka::Message;
use serde::Serialize;
use serde_json::Value;
use std::env;

pub struct Qyro;

impl Qyro {
    fn get_redis_url() -> String {
        let host = env::var("REDIS_HOST").unwrap_or("redis".to_string());
        let port = env::var("REDIS_PORT").unwrap_or("6379".to_string());
        format!("redis://{}:{}", host, port)
    }

    fn get_kafka_brokers() -> String {
        env::var("KAFKA_BOOTSTRAP_SERVERS").unwrap_or("kafka:9092".to_string())
    }

    pub fn set<T: Serialize>(key: &str, value: &T) -> redis::RedisResult<()> {
        let client = redis::Client::open(Self::get_redis_url())?;
        let mut con = client.get_connection()?;
        let val_str = serde_json::to_string(value).unwrap();
        con.set(key, val_str)
    }

    pub fn get(key: &str) -> redis::RedisResult<String> {
        let client = redis::Client::open(Self::get_redis_url())?;
        let mut con = client.get_connection()?;
        con.get(key)
    }

    pub async fn publish<T: Serialize>(topic: &str, message: &T) {
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", &Self::get_kafka_brokers())
            .create()
            .expect("Producer creation error");

        let payload = serde_json::to_string(message).unwrap();
        producer.send(
            FutureRecord::to(topic)
                .payload(&payload)
                .key("key"),
            std::time::Duration::from_secs(0),
        ).await.expect("Failed to send message");
    }

    // Note: Subscribe would return a stream, simplified here
}
