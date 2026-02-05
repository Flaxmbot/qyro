[package]
name = "qyro-chat-rust"
version = "1.0.0"
edition = "2021"
authors = ["Qyro Team"]

[dependencies]
redis = "0.25"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1