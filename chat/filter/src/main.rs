use rdkafka::consumer::{Consumer, StreamConsumer};
use rdkafka::ClientConfig;
use rdkafka::Message;
use futures::StreamExt;
use std::env;
#[path = "../qyro_adapters/rust_adapter.rs"]
mod qyro;

#[tokio::main]
async fn main() {
    println!("Filter service started");

    let brokers = env::var("KAFKA_BOOTSTRAP_SERVERS").unwrap_or("kafka:9092".to_string());

    let consumer: StreamConsumer = ClientConfig::new()
        .set("group.id", "rust_filter")
        .set("bootstrap.servers", &brokers)
        .set("auto.offset.reset", "earliest")
        .create()
        .expect("Consumer creation failed");

    consumer.subscribe(&["raw_messages"]).expect("Can't subscribe");

    let mut message_stream = consumer.stream();

    while let Some(message) = message_stream.next().await {
        match message {
            Ok(m) => {
                if let Some(payload) = m.payload() {
                    let text_str = std::str::from_utf8(payload).unwrap();
                    let mut json: serde_json::Value = serde_json::from_str(text_str).unwrap();

                    let text = json["text"].as_str().unwrap();
                    if text.contains("bad") {
                        json["text"] = serde_json::json!("***");
                    }

                    // Push to Redis List
                    // Access underlying redis via low-level or adapter extension
                    // My adapter doesn't have LPUSH.
                    // I will use redis crate directly here since I have it in deps.
                    let client = redis::Client::open("redis://redis:6379").unwrap();
                    let mut con = client.get_connection().unwrap();
                    let _: () = redis::cmd("RPUSH")
                        .arg("chat_history")
                        .arg(json.to_string())
                        .query(&mut con).unwrap();

                    println!("Processed: {}", json);
                }
            },
            Err(e) => println!("Error: {}", e),
        }
    }
}