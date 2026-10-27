//! Notification platform — Rust parallel of Python p9.
//!
//! Factory + Strategy + a thread-based fan-out. The fan-out is the closest
//! stdlib equivalent of Go's goroutine. Real Rust services use Tokio
//! (`tokio::spawn`) for cheaper async tasks, but `std::thread::spawn` is
//! fine for demonstration.

use std::collections::HashMap;
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

trait Channel: Send + Sync {
    fn name(&self) -> &'static str;
    fn send(&self, to: &str, body: &str);
}

struct EmailChannel;
impl Channel for EmailChannel {
    fn name(&self) -> &'static str { "email" }
    fn send(&self, to: &str, body: &str) {
        thread::sleep(Duration::from_millis(20));
        println!("  email -> {to}: {body}");
    }
}

struct SmsChannel;
impl Channel for SmsChannel {
    fn name(&self) -> &'static str { "sms" }
    fn send(&self, to: &str, body: &str) {
        thread::sleep(Duration::from_millis(10));
        println!("  sms   -> {to}: {body}");
    }
}

struct SlackChannel;
impl Channel for SlackChannel {
    fn name(&self) -> &'static str { "slack" }
    fn send(&self, to: &str, body: &str) {
        thread::sleep(Duration::from_millis(15));
        println!("  slack -> {to}: {body}");
    }
}

// --- registry (the factory) ---

struct Registry { channels: HashMap<String, Arc<dyn Channel>> }

impl Registry {
    fn new() -> Self { Self { channels: HashMap::new() } }
    fn register(&mut self, c: Arc<dyn Channel>) {
        self.channels.insert(c.name().into(), c);
    }
    fn get(&self, name: &str) -> Option<Arc<dyn Channel>> {
        self.channels.get(name).cloned()
    }

    fn broadcast(&self, channels: &[&str], to: &str, body: &str) {
        let mut handles = Vec::new();
        for &name in channels {
            match self.get(name) {
                None => println!("  unknown channel: {name}"),
                Some(c) => {
                    let to = to.to_string();
                    let body = body.to_string();
                    handles.push(thread::spawn(move || {
                        c.send(&to, &body);
                    }));
                }
            }
        }
        for h in handles { let _ = h.join(); }
    }
}

fn main() {
    let mut reg = Registry::new();
    reg.register(Arc::new(EmailChannel));
    reg.register(Arc::new(SmsChannel));
    reg.register(Arc::new(SlackChannel));

    println!("sequential:");
    for name in ["email", "sms", "slack"] {
        if let Some(c) = reg.get(name) {
            c.send("ada@example.com", "hello sequential");
        }
    }

    println!("\nparallel via threads:");
    let start = Instant::now();
    reg.broadcast(&["email", "sms", "slack", "carrier-pigeon"], "ada@example.com", "hello parallel");
    println!("done in {:?}", start.elapsed());
}
