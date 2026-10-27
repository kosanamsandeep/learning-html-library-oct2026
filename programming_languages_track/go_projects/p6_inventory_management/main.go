// Inventory management — Go parallel of Python p6.
//
// Lesson: Repository pattern via interfaces. The InventoryService depends on
// the Repository interface, not on a concrete store. Swap MemoryRepo for
// FileRepo without changing the service.
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sort"
)

type Item struct {
	SKU      string `json:"sku"`
	Name     string `json:"name"`
	Quantity int    `json:"quantity"`
	Reorder  int    `json:"reorder"`
}

// Repository is intentionally tiny — that's idiomatic Go. Big interfaces
// are an anti-pattern.
type Repository interface {
	Save(it Item) error
	Get(sku string) (Item, bool)
	All() []Item
}

// --- in-memory implementation ---

type MemoryRepo struct {
	store map[string]Item
}

func NewMemoryRepo() *MemoryRepo { return &MemoryRepo{store: map[string]Item{}} }

func (r *MemoryRepo) Save(it Item) error      { r.store[it.SKU] = it; return nil }
func (r *MemoryRepo) Get(sku string) (Item, bool) { it, ok := r.store[sku]; return it, ok }
func (r *MemoryRepo) All() []Item {
	out := make([]Item, 0, len(r.store))
	for _, it := range r.store {
		out = append(out, it)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].SKU < out[j].SKU })
	return out
}

// --- file-backed implementation (JSON file) ---

type FileRepo struct {
	path string
}

func (r *FileRepo) load() (map[string]Item, error) {
	data, err := os.ReadFile(r.path)
	if errors.Is(err, os.ErrNotExist) {
		return map[string]Item{}, nil
	}
	if err != nil {
		return nil, err
	}
	out := map[string]Item{}
	if len(data) == 0 {
		return out, nil
	}
	return out, json.Unmarshal(data, &out)
}

func (r *FileRepo) save(m map[string]Item) error {
	data, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(r.path, data, 0o644)
}

func (r *FileRepo) Save(it Item) error {
	m, err := r.load()
	if err != nil {
		return err
	}
	m[it.SKU] = it
	return r.save(m)
}

func (r *FileRepo) Get(sku string) (Item, bool) {
	m, err := r.load()
	if err != nil {
		return Item{}, false
	}
	it, ok := m[sku]
	return it, ok
}

func (r *FileRepo) All() []Item {
	m, _ := r.load()
	out := make([]Item, 0, len(m))
	for _, it := range m {
		out = append(out, it)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].SKU < out[j].SKU })
	return out
}

// --- service depends on Repository, not on a struct ---

type InventoryService struct{ repo Repository }

func NewInventoryService(r Repository) *InventoryService { return &InventoryService{repo: r} }

func (s *InventoryService) Stock(sku, name string, qty, reorder int) error {
	if qty < 0 {
		return errors.New("quantity must be >= 0")
	}
	return s.repo.Save(Item{SKU: sku, Name: name, Quantity: qty, Reorder: reorder})
}

func (s *InventoryService) LowStock() []Item {
	var out []Item
	for _, it := range s.repo.All() {
		if it.Quantity <= it.Reorder {
			out = append(out, it)
		}
	}
	return out
}

func main() {
	// Swap implementations without touching InventoryService.
	repo := NewMemoryRepo()
	// repo := &FileRepo{path: "stock.json"}

	svc := NewInventoryService(repo)
	_ = svc.Stock("MUG", "Coffee mug", 3, 5)
	_ = svc.Stock("BOOK", "Notebook", 50, 10)
	_ = svc.Stock("PEN", "Ballpoint", 2, 5)

	fmt.Println("low stock:")
	for _, it := range svc.LowStock() {
		fmt.Printf("  %s %q  qty=%d reorder=%d\n", it.SKU, it.Name, it.Quantity, it.Reorder)
	}
}
