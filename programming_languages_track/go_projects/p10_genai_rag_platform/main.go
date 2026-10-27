// GenAI RAG platform — Go parallel of Python p10.
//
// A skeleton end-to-end RAG flow: chunker -> embedder (interface) ->
// in-memory vector store -> ranker -> generator. The embedder is a
// pluggable interface: swap a real OpenAI client for the deterministic
// hash embedder used here without touching the rest of the pipeline.
//
// Concurrency: documents are embedded in parallel via a goroutine pool.
package main

import (
	"crypto/sha1"
	"fmt"
	"math"
	"sort"
	"strings"
	"sync"
)

// --- domain ---

type Chunk struct {
	DocID string
	Index int
	Text  string
}

type Embedding struct {
	Chunk  Chunk
	Vector []float64
}

// --- chunker ---

func chunkText(docID, text string, size int) []Chunk {
	words := strings.Fields(text)
	var out []Chunk
	for i := 0; i < len(words); i += size {
		end := i + size
		if end > len(words) {
			end = len(words)
		}
		out = append(out, Chunk{DocID: docID, Index: len(out), Text: strings.Join(words[i:end], " ")})
	}
	return out
}

// --- embedder interface (the seam) ---

type Embedder interface {
	Embed(text string) []float64
	Dim() int
}

// HashEmbedder is a deterministic, dependency-free fake. Hash each token
// into a small fixed-dim vector. Real systems plug an OpenAI / HF client here.
type HashEmbedder struct{ dim int }

func NewHashEmbedder(dim int) *HashEmbedder { return &HashEmbedder{dim: dim} }

func (e *HashEmbedder) Dim() int { return e.dim }

func (e *HashEmbedder) Embed(text string) []float64 {
	v := make([]float64, e.dim)
	for _, tok := range strings.Fields(strings.ToLower(text)) {
		sum := sha1.Sum([]byte(tok))
		for i := 0; i < e.dim; i++ {
			// folds 20 hash bytes across the dim positions
			v[i] += float64(sum[i%20]) / 255.0
		}
	}
	// L2 normalise
	var norm float64
	for _, x := range v {
		norm += x * x
	}
	norm = math.Sqrt(norm)
	if norm > 0 {
		for i := range v {
			v[i] /= norm
		}
	}
	return v
}

// --- vector store (in-memory, naive cosine search) ---

type VectorStore struct {
	mu    sync.Mutex
	items []Embedding
}

func (s *VectorStore) Add(e Embedding) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.items = append(s.items, e)
}

type Hit struct {
	Chunk Chunk
	Score float64
}

func (s *VectorStore) Search(query []float64, k int) []Hit {
	s.mu.Lock()
	items := append([]Embedding(nil), s.items...)
	s.mu.Unlock()

	hits := make([]Hit, len(items))
	for i, it := range items {
		hits[i] = Hit{Chunk: it.Chunk, Score: cosine(query, it.Vector)}
	}
	sort.Slice(hits, func(i, j int) bool { return hits[i].Score > hits[j].Score })
	if k > len(hits) {
		k = len(hits)
	}
	return hits[:k]
}

func cosine(a, b []float64) float64 {
	var dot float64
	for i := range a {
		dot += a[i] * b[i]
	}
	return dot
}

// --- generator (template, not an LLM) ---

func generate(query string, hits []Hit) string {
	var sb strings.Builder
	sb.WriteString("Q: ")
	sb.WriteString(query)
	sb.WriteString("\nA (cited):\n")
	for _, h := range hits {
		fmt.Fprintf(&sb, "  - [%s#%d] %.2f: %s\n", h.Chunk.DocID, h.Chunk.Index, h.Score, h.Chunk.Text)
	}
	return sb.String()
}

// --- pipeline: parallel embed + sequential ingest into the store ---

func ingest(emb Embedder, store *VectorStore, docs map[string]string, chunkSize int, workers int) {
	var allChunks []Chunk
	for id, body := range docs {
		allChunks = append(allChunks, chunkText(id, body, chunkSize)...)
	}

	jobs := make(chan Chunk, len(allChunks))
	var wg sync.WaitGroup
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for c := range jobs {
				store.Add(Embedding{Chunk: c, Vector: emb.Embed(c.Text)})
			}
		}()
	}
	for _, c := range allChunks {
		jobs <- c
	}
	close(jobs)
	wg.Wait()
}

func main() {
	docs := map[string]string{
		"doc1": "Go is a statically typed compiled language designed at Google. It has goroutines and channels for concurrency.",
		"doc2": "Rust is a systems language with ownership and borrowing. It guarantees memory safety without a garbage collector.",
		"doc3": "Python is dynamically typed and famous for its readability and rich ecosystem of AI libraries.",
	}

	emb := NewHashEmbedder(64)
	store := &VectorStore{}

	ingest(emb, store, docs, 8 /*words per chunk*/, 4 /*workers*/)

	for _, q := range []string{"memory safety without GC", "concurrency in compiled languages"} {
		hits := store.Search(emb.Embed(q), 2)
		fmt.Println(generate(q, hits))
	}
}
