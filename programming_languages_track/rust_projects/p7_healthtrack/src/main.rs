//! HealthTrack — Rust parallel of Python p7.
//!
//! Layered architecture skeleton: handler -> service -> repo -> domain.
//! Stays dependency-free for offline `cargo run` — so instead of an actual
//! HTTP server we drive a few "requests" from `main`. In a real app you'd
//! pull in `axum` (Tokio-based) and the request struct would come from a
//! web framework instead of a constructor.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};

#[derive(Debug, Clone)]
struct Record {
    id: u64,
    user: String,
    weight_kg: f64,
    recorded: String, // ISO-ish; using stdlib only
}

struct RecordRepo {
    store: HashMap<u64, Record>,
    next_id: u64,
}

impl RecordRepo {
    fn new() -> Self { Self { store: HashMap::new(), next_id: 1 } }

    fn save(&mut self, mut rec: Record) -> Record {
        rec.id = self.next_id;
        self.next_id += 1;
        self.store.insert(rec.id, rec.clone());
        rec
    }

    fn by_user(&self, user: &str) -> Vec<Record> {
        let mut out: Vec<Record> = self.store.values()
            .filter(|r| r.user == user).cloned().collect();
        out.sort_by_key(|r| r.id);
        out
    }
}

struct HealthService { repo: Arc<Mutex<RecordRepo>> }

struct RecordRequest { user: String, weight_kg: f64 }

impl HealthService {
    fn add(&self, req: RecordRequest) -> Result<Record, String> {
        if req.user.trim().is_empty() { return Err("user required".into()); }
        if req.weight_kg <= 0.0       { return Err("weight must be positive".into()); }
        let rec = Record {
            id: 0,
            user: req.user,
            weight_kg: req.weight_kg,
            recorded: "2026-06-07T10:00:00Z".into(),
        };
        Ok(self.repo.lock().unwrap().save(rec))
    }

    fn by_user(&self, user: &str) -> Vec<Record> {
        self.repo.lock().unwrap().by_user(user)
    }
}

// "Handler" simulation — pretend each call is an HTTP request.
fn simulate_post(svc: &HealthService, body: RecordRequest) {
    match svc.add(body) {
        Ok(r)  => println!("201 {{ id: {}, user: {}, weight_kg: {} }}", r.id, r.user, r.weight_kg),
        Err(e) => println!("400 {{ error: \"{e}\" }}"),
    }
}

fn simulate_get(svc: &HealthService, user: &str) {
    let rs = svc.by_user(user);
    println!("200 [");
    for r in &rs {
        println!("  {{ id: {}, weight_kg: {}, recorded: {} }}", r.id, r.weight_kg, r.recorded);
    }
    println!("]");
}

fn main() {
    let svc = HealthService { repo: Arc::new(Mutex::new(RecordRepo::new())) };

    simulate_post(&svc, RecordRequest { user: "ada".into(), weight_kg: 62.0 });
    simulate_post(&svc, RecordRequest { user: "ada".into(), weight_kg: 61.5 });
    simulate_post(&svc, RecordRequest { user: "".into(),    weight_kg: 70.0 }); // bad
    simulate_get(&svc, "ada");
}
