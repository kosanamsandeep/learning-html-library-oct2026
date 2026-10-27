//! Student-management demo — Rust parallel of Python p1.
//!
//! Mirrors the service-layer / encapsulation lesson:
//!   - `Student` is a plain `struct` with `#[derive(Debug, Clone)]`.
//!   - `StudentService` owns the `HashMap` store.
//!   - Errors come back as `Result<T, String>` (a real app would use a
//!     custom error enum, but `String` keeps the demo dependency-free).

use std::collections::HashMap;

#[derive(Debug, Clone)]
struct Student {
    id: u64,
    name: String,
    grade: u32,
}

struct StudentService {
    students: HashMap<u64, Student>,
    next_id: u64,
}

impl StudentService {
    fn new() -> Self {
        Self { students: HashMap::new(), next_id: 1 }
    }

    fn add(&mut self, name: &str, grade: u32) -> Result<Student, String> {
        if name.trim().is_empty() {
            return Err("name is required".into());
        }
        let s = Student { id: self.next_id, name: name.to_string(), grade };
        self.students.insert(s.id, s.clone());
        self.next_id += 1;
        Ok(s)
    }

    fn get(&self, id: u64) -> Option<&Student> {
        self.students.get(&id)
    }

    fn list(&self) -> Vec<&Student> {
        let mut out: Vec<&Student> = self.students.values().collect();
        out.sort_by_key(|s| s.id);
        out
    }

    fn average_grade(&self) -> f64 {
        if self.students.is_empty() {
            return 0.0;
        }
        let total: u32 = self.students.values().map(|s| s.grade).sum();
        total as f64 / self.students.len() as f64
    }
}

fn main() {
    let mut svc = StudentService::new();

    for (name, grade) in [("Ada", 91), ("Bob", 88), ("Cy", 79)] {
        match svc.add(name, grade) {
            Ok(s)  => println!("added: Student#{} {} (grade {})", s.id, s.name, s.grade),
            Err(e) => println!("error: {e}"),
        }
    }

    println!("\nall students:");
    for s in svc.list() {
        println!("  Student#{} {} (grade {})", s.id, s.name, s.grade);
    }

    println!("\naverage grade: {:.2}", svc.average_grade());
    if let Some(s) = svc.get(1) {
        println!("lookup id=1 -> {}", s.name);
    }
}
