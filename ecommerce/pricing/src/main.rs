use std::{thread, time};
#[path = "../qyro_adapters/rust_adapter.rs"]
mod qyro;

#[tokio::main]
async fn main() {
    println!("Pricing service started");
    loop {
        let discount = 0.9;
        println!("Setting discount to {}", discount);

        let _ = qyro::Qyro::set("discount_factor", &discount);

        let _ = qyro::Qyro::publish("logs", &serde_json::json!({
            "service": "pricing",
            "msg": "Updated discount"
        })).await;

        thread::sleep(time::Duration::from_secs(10));
    }
}