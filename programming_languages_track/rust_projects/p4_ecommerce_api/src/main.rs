//! E-commerce API — Rust parallel of Python p4.
//!
//! DTO pattern: separate internal `Product` / `Order` from the wire-shape
//! `ProductDto` / `OrderRequestDto`. In a real Rust app you'd use `serde` to
//! derive serialisation; this demo stays dependency-free and "renders" JSON
//! manually so you can `cargo run` offline.

use std::collections::HashMap;

#[derive(Debug, Clone)]
struct Product {
    id: u64,
    name: String,
    price_cent: i64,
    stock: i64,
    #[allow(dead_code)]
    internal_sku: String, // never crosses the API boundary
}

#[derive(Debug, Clone)]
struct ProductDto { id: u64, name: String, price: f64, stock: i64 }

impl ProductDto {
    fn from_domain(p: &Product) -> Self {
        Self {
            id: p.id,
            name: p.name.clone(),
            price: p.price_cent as f64 / 100.0,
            stock: p.stock,
        }
    }
    fn to_json(&self) -> String {
        format!(
            "{{\"id\":{},\"name\":\"{}\",\"price\":{:.2},\"stock\":{}}}",
            self.id, self.name, self.price, self.stock
        )
    }
}

#[derive(Debug)]
struct OrderLine { product_id: u64, quantity: i64 }

#[derive(Debug)]
struct OrderResponseDto { order_id: u64, total_price: f64 }

struct Catalog {
    products: HashMap<u64, Product>,
    next_order: u64,
}

impl Catalog {
    fn new() -> Self { Self { products: HashMap::new(), next_order: 1 } }

    fn add(&mut self, p: Product) { self.products.insert(p.id, p); }

    fn place_order(&mut self, lines: &[OrderLine]) -> Result<OrderResponseDto, String> {
        if lines.is_empty() { return Err("empty order".into()); }

        let mut total_cent: i64 = 0;
        // Validate first, then mutate — keeps the operation atomic on failure.
        for line in lines {
            let p = self.products.get(&line.product_id)
                .ok_or_else(|| format!("unknown product {}", line.product_id))?;
            if line.quantity <= 0 || line.quantity > p.stock {
                return Err(format!("bad quantity for {}", line.product_id));
            }
            total_cent += line.quantity * p.price_cent;
        }
        for line in lines {
            let p = self.products.get_mut(&line.product_id).unwrap();
            p.stock -= line.quantity;
        }

        let id = self.next_order;
        self.next_order += 1;
        Ok(OrderResponseDto { order_id: id, total_price: total_cent as f64 / 100.0 })
    }
}

fn main() {
    let mut c = Catalog::new();
    c.add(Product { id: 1, name: "Mug".into(),  price_cent: 999,  stock: 50, internal_sku: "MUG".into() });
    c.add(Product { id: 2, name: "Book".into(), price_cent: 1499, stock: 30, internal_sku: "BOOK_STD".into() });

    println!("GET /products =>");
    let mut dtos: Vec<ProductDto> = c.products.values().map(ProductDto::from_domain).collect();
    dtos.sort_by_key(|d| d.id);
    let body: Vec<String> = dtos.iter().map(|d| d.to_json()).collect();
    println!("[{}]", body.join(","));

    let lines = [
        OrderLine { product_id: 1, quantity: 2 },
        OrderLine { product_id: 2, quantity: 1 },
    ];
    match c.place_order(&lines) {
        Ok(r)  => println!("\nPOST /orders =>\n{{\"order_id\":{},\"total_price\":{:.2}}}", r.order_id, r.total_price),
        Err(e) => println!("error: {e}"),
    }
}
