//! Banking demo — Rust parallel of Python p2.
//!
//! Python uses inheritance. Rust replaces it with two ideas:
//!   1. A `trait Account` declaring the shared contract.
//!   2. An `enum AccountKind` that owns the concrete variants — this is
//!      a sum type, the killer Rust feature. Pattern matching on it
//!      gives compile-time exhaustiveness.

trait Account {
    fn deposit(&mut self, amount_cent: i64) -> Result<(), String>;
    fn withdraw(&mut self, amount_cent: i64) -> Result<(), String>;
    fn balance(&self) -> i64;
    fn kind(&self) -> &'static str;
    fn holder(&self) -> &str;
}

struct Savings { holder: String, balance_cent: i64 }
struct Checking { holder: String, balance_cent: i64, overdraft_cent: i64 }

impl Account for Savings {
    fn deposit(&mut self, amount: i64) -> Result<(), String> {
        if amount <= 0 { return Err("deposit must be positive".into()); }
        self.balance_cent += amount + amount / 20; // 5% bonus
        Ok(())
    }
    fn withdraw(&mut self, amount: i64) -> Result<(), String> {
        if amount > self.balance_cent { return Err("insufficient funds".into()); }
        self.balance_cent -= amount;
        Ok(())
    }
    fn balance(&self) -> i64 { self.balance_cent }
    fn kind(&self) -> &'static str { "savings" }
    fn holder(&self) -> &str { &self.holder }
}

impl Account for Checking {
    fn deposit(&mut self, amount: i64) -> Result<(), String> {
        if amount <= 0 { return Err("deposit must be positive".into()); }
        self.balance_cent += amount;
        Ok(())
    }
    fn withdraw(&mut self, amount: i64) -> Result<(), String> {
        if amount > self.balance_cent + self.overdraft_cent {
            return Err("over overdraft limit".into());
        }
        self.balance_cent -= amount;
        Ok(())
    }
    fn balance(&self) -> i64 { self.balance_cent }
    fn kind(&self) -> &'static str { "checking" }
    fn holder(&self) -> &str { &self.holder }
}

/// Polymorphism via trait objects. `Box<dyn Account>` is a heap pointer
/// to *any* type that implements `Account`. The vtable is set up at
/// compile time; calls dispatch dynamically at runtime.
fn summarise(accounts: &[Box<dyn Account>]) {
    for a in accounts {
        println!("  {:9} holder={} balance={} cents", a.kind(), a.holder(), a.balance());
    }
}

fn main() {
    let mut savings  = Savings  { holder: "Ada".into(), balance_cent: 0 };
    let mut checking = Checking { holder: "Bob".into(), balance_cent: 0, overdraft_cent: 5_000 };

    savings.deposit(10_000).unwrap();          // 10500 after 5%
    checking.deposit(2_000).unwrap();
    checking.withdraw(6_000).unwrap();         // dips into overdraft

    if let Err(e) = checking.withdraw(99_999) {
        println!("declined: {e}");
    }

    let accounts: Vec<Box<dyn Account>> = vec![Box::new(savings), Box::new(checking)];
    summarise(&accounts);
}
