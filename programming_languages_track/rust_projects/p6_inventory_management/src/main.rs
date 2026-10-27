//! Inventory management — Rust parallel of Python p6.
//!
//! Repository pattern via a trait + a trait object. The service owns
//! `Box<dyn Repository>` so we can pick the implementation at runtime.

use std::collections::HashMap;

#[derive(Debug, Clone)]
struct Item {
    sku: String,
    name: String,
    quantity: i64,
    reorder: i64,
}

trait Repository {
    fn save(&mut self, it: Item);
    fn get(&self, sku: &str) -> Option<&Item>;
    fn all(&self) -> Vec<&Item>;
}

// --- in-memory implementation ---

struct MemoryRepo { store: HashMap<String, Item> }

impl MemoryRepo {
    fn new() -> Self { Self { store: HashMap::new() } }
}

impl Repository for MemoryRepo {
    fn save(&mut self, it: Item) {
        self.store.insert(it.sku.clone(), it);
    }
    fn get(&self, sku: &str) -> Option<&Item> {
        self.store.get(sku)
    }
    fn all(&self) -> Vec<&Item> {
        let mut out: Vec<&Item> = self.store.values().collect();
        out.sort_by(|a, b| a.sku.cmp(&b.sku));
        out
    }
}

// --- a second implementation: a counting decorator (pattern preview) ---
// Wraps any repository and counts saves. Equivalent to Python decorators.

struct CountingRepo {
    inner: Box<dyn Repository>,
    saves: u64,
}

impl Repository for CountingRepo {
    fn save(&mut self, it: Item) { self.saves += 1; self.inner.save(it); }
    fn get(&self, sku: &str) -> Option<&Item> { self.inner.get(sku) }
    fn all(&self) -> Vec<&Item> { self.inner.all() }
}

// --- service depends on the trait ---

struct InventoryService { repo: Box<dyn Repository> }

impl InventoryService {
    fn stock(&mut self, sku: &str, name: &str, quantity: i64, reorder: i64) -> Result<(), String> {
        if quantity < 0 { return Err("quantity must be >= 0".into()); }
        self.repo.save(Item { sku: sku.into(), name: name.into(), quantity, reorder });
        Ok(())
    }

    fn low_stock(&self) -> Vec<&Item> {
        self.repo.all().into_iter().filter(|it| it.quantity <= it.reorder).collect()
    }
}

fn main() {
    // Pick the implementation at runtime — same idea as Go's interface.
    let inner: Box<dyn Repository> = Box::new(MemoryRepo::new());
    let counting = Box::new(CountingRepo { inner, saves: 0 });
    let mut svc = InventoryService { repo: counting };

    svc.stock("MUG",  "Coffee mug", 3,  5).unwrap();
    svc.stock("BOOK", "Notebook",   50, 10).unwrap();
    svc.stock("PEN",  "Ballpoint",  2,  5).unwrap();

    println!("low stock:");
    for it in svc.low_stock() {
        println!("  {} \"{}\" qty={} reorder={}", it.sku, it.name, it.quantity, it.reorder);
    }
}
