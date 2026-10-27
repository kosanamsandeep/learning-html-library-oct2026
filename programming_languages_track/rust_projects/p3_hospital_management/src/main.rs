//! Hospital management — Rust parallel of Python p3.
//!
//! Composition with nested structs. `Option<&Doctor>` replaces Python's
//! `Optional[Doctor]`, and we use `iter_mut()` when we need to mutate
//! something inside a nested collection.

use std::collections::HashMap;

#[derive(Debug, Clone)]
struct Appointment {
    patient: String,
    when: String, // keep as string to stay dependency-free
}

#[derive(Debug)]
struct Doctor {
    id: u64,
    name: String,
    specialty: String,
    appointments: Vec<Appointment>,
}

impl Doctor {
    fn book(&mut self, patient: &str, when: &str) {
        self.appointments.push(Appointment { patient: patient.into(), when: when.into() });
    }
}

#[derive(Debug)]
struct Department {
    name: String,
    doctors: Vec<Doctor>,
}

impl Department {
    fn find_doctor_mut(&mut self, id: u64) -> Option<&mut Doctor> {
        self.doctors.iter_mut().find(|d| d.id == id)
    }
}

#[derive(Debug)]
struct Hospital {
    name: String,
    departments: HashMap<String, Department>,
}

impl Hospital {
    fn new(name: &str) -> Self {
        Self { name: name.into(), departments: HashMap::new() }
    }

    fn add_department(&mut self, name: &str) {
        self.departments.insert(
            name.into(),
            Department { name: name.into(), doctors: Vec::new() },
        );
    }

    fn book(&mut self, dept: &str, doctor_id: u64, patient: &str, when: &str)
        -> Result<(), String>
    {
        let d = self.departments.get_mut(dept)
            .ok_or_else(|| format!("no such department: {dept}"))?;
        let doc = d.find_doctor_mut(doctor_id)
            .ok_or("no such doctor")?;
        doc.book(patient, when);
        Ok(())
    }
}

fn main() {
    let mut h = Hospital::new("Mercy General");
    h.add_department("Cardiology");
    let cardio = h.departments.get_mut("Cardiology").unwrap();
    cardio.doctors.push(Doctor { id: 1, name: "Dr. Lin".into(), specialty: "interventional".into(), appointments: vec![] });
    cardio.doctors.push(Doctor { id: 2, name: "Dr. Patel".into(), specialty: "imaging".into(),       appointments: vec![] });

    h.book("Cardiology", 1, "Ada", "2026-06-15 09:30").unwrap();
    h.book("Cardiology", 1, "Bob", "2026-06-15 10:30").unwrap();
    if let Err(e) = h.book("Neurology", 1, "Cy", "2026-06-15 11:30") {
        println!("expected error: {e}");
    }

    println!("\n{}", h.name);
    for dept in h.departments.values() {
        println!("  {}", dept.name);
        for doc in &dept.doctors {
            println!("    {} ({}) - {} appts", doc.name, doc.specialty, doc.appointments.len());
            for a in &doc.appointments {
                println!("      {} @ {}", a.patient, a.when);
            }
        }
    }
}
