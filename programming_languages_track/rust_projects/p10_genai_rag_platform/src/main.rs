//! GenAI RAG platform — Rust parallel of Python p10.
//!
//! End-to-end RAG skeleton: chunker -> Embedder trait -> in-memory vector
//! store (Arc<Mutex<...>>) -> ranker -> generator. Parallel ingest with
//! `std::thread::spawn`. No third-party deps.
//!
//! In production you'd swap `HashEmbedder` for an OpenAI/Ollama client
//! crate, and the in-memory store for a real ANN index (HNSW, FAISS, or
//! a hosted vector DB like Qdrant — all Rust-friendly).

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::sync::{Arc, Mutex};
use std::thread;

#[derive(Debug, Clone)]
struct Chunk { doc_id: String, index: usize, text: String }

#[derive(Debug, Clone)]
struct Embedding { chunk: Chunk, vector: Vec<f64> }

fn chunk_text(doc_id: &str, text: &str, size: usize) -> Vec<Chunk> {
    let words: Vec<&str> = text.split_whitespace().collect();
    let mut out = Vec::new();
    let mut i = 0;
    while i < words.len() {
        let end = (i + size).min(words.len());
        out.push(Chunk {
            doc_id: doc_id.into(),
            index: out.len(),
            text: words[i..end].join(" "),
        });
        i += size;
    }
    out
}

trait Embedder: Send + Sync {
    fn embed(&self, text: &str) -> Vec<f64>;
    fn dim(&self) -> usize;
}

struct HashEmbedder { dim: usize }

impl HashEmbedder { fn new(dim: usize) -> Self { Self { dim } } }

impl Embedder for HashEmbedder {
    fn dim(&self) -> usize { self.dim }
    fn embed(&self, text: &str) -> Vec<f64> {
        let mut v = vec![0f64; self.dim];
        for tok in text.to_lowercase().split_whitespace() {
            let mut h = DefaultHasher::new();
            tok.hash(&mut h);
            let mut x = h.finish();
            for slot in v.iter_mut() {
                // pseudo-spread the hash across the vector
                *slot += ((x & 0xff) as f64) / 255.0;
                x = x.wrapping_mul(2862933555777941757).wrapping_add(3037000493);
            }
        }
        let norm = v.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norm > 0.0 { for x in v.iter_mut() { *x /= norm; } }
        v
    }
}

struct VectorStore { items: Vec<Embedding> }

impl VectorStore {
    fn new() -> Self { Self { items: Vec::new() } }

    fn add(&mut self, e: Embedding) { self.items.push(e); }

    fn search(&self, query: &[f64], k: usize) -> Vec<(Chunk, f64)> {
        let mut hits: Vec<(Chunk, f64)> = self.items.iter()
            .map(|it| (it.chunk.clone(), cosine(query, &it.vector)))
            .collect();
        hits.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        hits.truncate(k);
        hits
    }
}

fn cosine(a: &[f64], b: &[f64]) -> f64 {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

fn generate(query: &str, hits: &[(Chunk, f64)]) -> String {
    let mut out = format!("Q: {query}\nA (cited):\n");
    for (c, score) in hits {
        out.push_str(&format!("  - [{}#{}] {:.2}: {}\n", c.doc_id, c.index, score, c.text));
    }
    out
}

fn ingest_parallel(emb: Arc<dyn Embedder>, store: Arc<Mutex<VectorStore>>, chunks: Vec<Chunk>, workers: usize) {
    let work = Arc::new(Mutex::new(chunks));
    let mut handles = Vec::with_capacity(workers);
    for _ in 0..workers {
        let work = Arc::clone(&work);
        let emb = Arc::clone(&emb);
        let store = Arc::clone(&store);
        handles.push(thread::spawn(move || {
            loop {
                let next = {
                    let mut q = work.lock().unwrap();
                    q.pop()
                };
                match next {
                    None => break,
                    Some(c) => {
                        let v = emb.embed(&c.text);
                        store.lock().unwrap().add(Embedding { chunk: c, vector: v });
                    }
                }
            }
        }));
    }
    for h in handles { let _ = h.join(); }
}

fn main() {
    let docs = [
        ("doc1", "Go is a statically typed compiled language designed at Google. It has goroutines and channels for concurrency."),
        ("doc2", "Rust is a systems language with ownership and borrowing. It guarantees memory safety without a garbage collector."),
        ("doc3", "Python is dynamically typed and famous for its readability and rich ecosystem of AI libraries."),
    ];

    let mut all_chunks = Vec::new();
    for (id, body) in docs { all_chunks.extend(chunk_text(id, body, 8)); }

    let emb: Arc<dyn Embedder> = Arc::new(HashEmbedder::new(64));
    let store = Arc::new(Mutex::new(VectorStore::new()));

    ingest_parallel(Arc::clone(&emb), Arc::clone(&store), all_chunks, 4);

    for q in ["memory safety without GC", "concurrency in compiled languages"] {
        let qv = emb.embed(q);
        let hits = store.lock().unwrap().search(&qv, 2);
        println!("{}", generate(q, &hits));
    }
}
