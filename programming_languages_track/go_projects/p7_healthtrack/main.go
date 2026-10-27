// HealthTrack — Go parallel of Python p7.
//
// Layered architecture: HTTP handler -> service -> repository -> domain model.
// Uses the standard library's net/http with no third-party deps.
//
// Try it:
//   go run .                            # starts on :8080
//   curl -X POST localhost:8080/records -d '{"user":"ada","weight_kg":62}' \
//        -H 'content-type: application/json'
//   curl localhost:8080/records?user=ada
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"
)

// --- domain ---

type Record struct {
	ID        int       `json:"id"`
	User      string    `json:"user"`
	WeightKg  float64   `json:"weight_kg"`
	Recorded  time.Time `json:"recorded"`
}

// --- repository (in-memory, thread-safe) ---

type RecordRepo struct {
	mu     sync.Mutex
	store  map[int]Record
	nextID int
}

func NewRecordRepo() *RecordRepo { return &RecordRepo{store: map[int]Record{}, nextID: 1} }

func (r *RecordRepo) Save(rec Record) Record {
	r.mu.Lock()
	defer r.mu.Unlock()
	rec.ID = r.nextID
	r.nextID++
	r.store[rec.ID] = rec
	return rec
}

func (r *RecordRepo) ByUser(user string) []Record {
	r.mu.Lock()
	defer r.mu.Unlock()
	var out []Record
	for _, rec := range r.store {
		if rec.User == user {
			out = append(out, rec)
		}
	}
	return out
}

// --- service ---

type HealthService struct{ repo *RecordRepo }

type RecordRequestDTO struct {
	User     string  `json:"user"`
	WeightKg float64 `json:"weight_kg"`
}

func (s *HealthService) Add(req RecordRequestDTO) (Record, error) {
	if req.User == "" {
		return Record{}, fmt.Errorf("user required")
	}
	if req.WeightKg <= 0 {
		return Record{}, fmt.Errorf("weight must be positive")
	}
	return s.repo.Save(Record{User: req.User, WeightKg: req.WeightKg, Recorded: time.Now()}), nil
}

// --- handlers ---

type API struct{ svc *HealthService }

func (a *API) records(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodPost:
		var req RecordRequestDTO
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "bad json", http.StatusBadRequest)
			return
		}
		rec, err := a.svc.Add(req)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		w.Header().Set("content-type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_ = json.NewEncoder(w).Encode(rec)
	case http.MethodGet:
		user := r.URL.Query().Get("user")
		if user == "" {
			http.Error(w, "user query param required", http.StatusBadRequest)
			return
		}
		w.Header().Set("content-type", "application/json")
		_ = json.NewEncoder(w).Encode(a.svc.repo.ByUser(user))
	default:
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	}
}

func main() {
	repo := NewRecordRepo()
	svc := &HealthService{repo: repo}
	api := &API{svc: svc}

	mux := http.NewServeMux()
	mux.HandleFunc("/records", api.records)

	addr := ":8080"
	log.Println("healthtrack listening on", addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}
