//! Contact management — Rust parallel of Python p5.
//!
//! Validation that collects every error rather than failing on the first.
//! Returns `Result<(), Vec<String>>`. A real app would typically define a
//! `ValidationError` enum, but `Vec<String>` keeps this demo dep-free.

#[derive(Debug)]
struct Address { line1: String, city: String, country: String, postcode: String }

#[derive(Debug)]
enum PhoneKind { Mobile, Work, Home }

impl PhoneKind {
    fn parse(s: &str) -> Option<Self> {
        match s { "mobile" => Some(Self::Mobile), "work" => Some(Self::Work), "home" => Some(Self::Home), _ => None }
    }
}

#[derive(Debug)]
struct Phone { kind: Option<PhoneKind>, raw_kind: String, number: String }

#[derive(Debug)]
struct Email { address: String, primary: bool }

#[derive(Debug)]
struct Contact {
    id: u64,
    first_name: String,
    last_name: String,
    addresses: Vec<Address>,
    phones: Vec<Phone>,
    emails: Vec<Email>,
}

fn looks_like_email(s: &str) -> bool {
    // Tiny check, no regex crate required:
    // exactly one '@', and '.' somewhere after it, no whitespace.
    if s.chars().any(char::is_whitespace) { return false; }
    let at: Vec<_> = s.match_indices('@').collect();
    if at.len() != 1 { return false; }
    let (i, _) = at[0];
    if i == 0 || i == s.len() - 1 { return false; }
    s[i + 1..].contains('.')
}

impl Contact {
    fn validate(&self) -> Result<(), Vec<String>> {
        let mut errs = Vec::new();
        if self.first_name.trim().is_empty() { errs.push("first name required".into()); }
        if self.last_name.trim().is_empty()  { errs.push("last name required".into());  }
        if self.emails.is_empty()            { errs.push("at least one email required".into()); }

        let mut primaries = 0;
        for (i, e) in self.emails.iter().enumerate() {
            if !looks_like_email(&e.address) {
                errs.push(format!("emails[{i}]: invalid format \"{}\"", e.address));
            }
            if e.primary { primaries += 1; }
        }
        if !self.emails.is_empty() && primaries != 1 {
            errs.push(format!("exactly one primary email required, got {primaries}"));
        }

        for (i, p) in self.phones.iter().enumerate() {
            if p.number.len() < 6 { errs.push(format!("phones[{i}]: number too short")); }
            if p.kind.is_none()   { errs.push(format!("phones[{i}]: bad kind \"{}\"", p.raw_kind)); }
        }

        if errs.is_empty() { Ok(()) } else { Err(errs) }
    }
}

fn main() {
    let good = Contact {
        id: 1, first_name: "Ada".into(), last_name: "Lovelace".into(),
        addresses: vec![Address { line1: "10 King St".into(), city: "London".into(), country: "UK".into(), postcode: "SW1".into() }],
        phones: vec![Phone { kind: PhoneKind::parse("mobile"), raw_kind: "mobile".into(), number: "+447700900123".into() }],
        emails: vec![Email { address: "ada@example.com".into(), primary: true }],
    };
    let bad = Contact {
        id: 2, first_name: "".into(), last_name: "Hopper".into(),
        addresses: vec![],
        phones: vec![Phone { kind: PhoneKind::parse("fax"), raw_kind: "fax".into(), number: "12".into() }],
        emails: vec![
            Email { address: "not-an-email".into(), primary: true },
            Email { address: "h2@example.com".into(),  primary: true }, // 2 primaries
        ],
    };

    for c in [good, bad] {
        match c.validate() {
            Ok(())  => println!("{} {}: OK", c.first_name, c.last_name),
            Err(es) => println!("{} {}: INVALID -> {}", c.first_name, c.last_name, es.join("; ")),
        }
    }
}
