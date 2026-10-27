//! Authentication platform — Rust parallel of Python p8.
//!
//! Pluggable strategies via a trait + dependency injection.
//!
//! NOTE: the password "hash" here is a tiny FNV-style fold for demo
//! purposes only — it is intentionally weak so this file stays dependency
//! free. In a real project use the `argon2` or `bcrypt` crate.

use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
struct Identity { user_id: u64, name: String }

trait Authenticator {
    fn authenticate(&self, creds: &HashMap<&str, &str>) -> Result<Identity, String>;
}

// --- demo "hash" ---
fn weak_hash(pw: &str) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in pw.bytes() {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

fn demo_credential(label: &str) -> String {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system clock should be after unix epoch")
        .as_nanos();
    format!("demo-{label}-{now:x}")
}

// --- password strategy ---

struct PasswordAuth {
    users: HashMap<String, u64>, // username -> hash
    ids: HashMap<String, Identity>,
}

impl PasswordAuth {
    fn new() -> Self { Self { users: HashMap::new(), ids: HashMap::new() } }
    fn register(&mut self, name: &str, pw: &str, id: u64) {
        self.users.insert(name.into(), weak_hash(pw));
        self.ids.insert(name.into(), Identity { user_id: id, name: name.into() });
    }
}

impl Authenticator for PasswordAuth {
    fn authenticate(&self, creds: &HashMap<&str, &str>) -> Result<Identity, String> {
        let user = creds.get("username").copied().ok_or("missing username")?;
        let pw   = creds.get("password").copied().ok_or("missing password")?;
        match self.users.get(user) {
            Some(h) if *h == weak_hash(pw) => Ok(self.ids[user].clone()),
            _ => Err("invalid credentials".into()),
        }
    }
}

// --- api-key strategy ---

struct ApiKeyAuth { keys: HashMap<String, Identity> }

impl ApiKeyAuth {
    fn new() -> Self { Self { keys: HashMap::new() } }
    fn issue(&mut self, id: u64, name: &str) -> String {
        let key = demo_credential("api-key");
        self.keys.insert(key.clone(), Identity { user_id: id, name: name.into() });
        key
    }
}

impl Authenticator for ApiKeyAuth {
    fn authenticate(&self, creds: &HashMap<&str, &str>) -> Result<Identity, String> {
        let key = creds.get("api_key").copied().ok_or("missing api_key")?;
        self.keys.get(key).cloned().ok_or_else(|| "unknown api key".into())
    }
}

// --- service ---

struct AuthService<'a> { a: &'a dyn Authenticator }

impl AuthService<'_> {
    fn login(&self, creds: HashMap<&str, &str>) {
        match self.a.authenticate(&creds) {
            Ok(id)  => println!("ALLOW: user_id={} name={}", id.user_id, id.name),
            Err(e)  => println!("DENY: {e}"),
        }
    }
}

fn main() {
    let mut pw = PasswordAuth::new();
    let ada_password = demo_credential("ada");
    let bob_password = demo_credential("bob");
    pw.register("ada", ada_password.as_str(), 1);
    pw.register("bob", bob_password.as_str(), 2);

    let mut api = ApiKeyAuth::new();
    let ada_api_key = api.issue(1, "ada");

    let pw_svc = AuthService { a: &pw };
    pw_svc.login(HashMap::from([("username", "ada"), ("password", ada_password.as_str())]));
    let invalid_password = demo_credential("invalid");
    pw_svc.login(HashMap::from([("username", "ada"), ("password", invalid_password.as_str())]));

    let api_svc = AuthService { a: &api };
    api_svc.login(HashMap::from([("api_key", ada_api_key.as_str())]));
    let unknown_api_key = demo_credential("unknown-api-key");
    api_svc.login(HashMap::from([("api_key", unknown_api_key.as_str())]));
}
