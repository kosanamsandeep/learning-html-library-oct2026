// E-commerce API demo — Go parallel of Python p4.
//
// Lesson: DTO pattern. The internal Product / Order is *not* the same as the
// JSON shape clients see. Separating the two lets you change either without
// breaking the other.
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"strings"
)

// --- internal domain ---

type Product struct {
	ID          int
	Name        string
	PriceCent   int
	StockCount  int
	internalSKU string // private — never goes out via API
}

type Order struct {
	ID    int
	Items []OrderLine
}

type OrderLine struct {
	ProductID int
	Quantity  int
	UnitCent  int
}

// --- DTOs (the API contract) ---
// Note the json tags — they decide what wire field name + visibility apply.

type ProductDTO struct {
	ID    int     `json:"id"`
	Name  string  `json:"name"`
	Price float64 `json:"price"`
	Stock int     `json:"stock"`
}

type OrderRequestDTO struct {
	Items []OrderLineDTO `json:"items"`
}

type OrderLineDTO struct {
	ProductID int `json:"product_id"`
	Quantity  int `json:"quantity"`
}

type OrderResponseDTO struct {
	OrderID    int     `json:"order_id"`
	TotalPrice float64 `json:"total_price"`
}

// Mappers — the seam between the wire format and the domain.

func toProductDTO(p Product) ProductDTO {
	return ProductDTO{
		ID:    p.ID,
		Name:  p.Name,
		Price: float64(p.PriceCent) / 100,
		Stock: p.StockCount,
	}
}

// --- service ---

type Catalog struct {
	products map[int]Product
	nextOrder int
}

func NewCatalog() *Catalog { return &Catalog{products: map[int]Product{}, nextOrder: 1} }

func (c *Catalog) Add(p Product) { c.products[p.ID] = p }

func (c *Catalog) PlaceOrder(req OrderRequestDTO) (OrderResponseDTO, error) {
	if len(req.Items) == 0 {
		return OrderResponseDTO{}, errors.New("empty order")
	}
	totalCent := 0
	for _, line := range req.Items {
		p, ok := c.products[line.ProductID]
		if !ok {
			return OrderResponseDTO{}, fmt.Errorf("unknown product %d", line.ProductID)
		}
		if line.Quantity <= 0 || line.Quantity > p.StockCount {
			return OrderResponseDTO{}, fmt.Errorf("bad quantity for %d", line.ProductID)
		}
		totalCent += line.Quantity * p.PriceCent
		p.StockCount -= line.Quantity
		c.products[p.ID] = p
	}
	id := c.nextOrder
	c.nextOrder++
	return OrderResponseDTO{OrderID: id, TotalPrice: float64(totalCent) / 100}, nil
}

func main() {
	c := NewCatalog()
	c.Add(Product{ID: 1, Name: "Mug", PriceCent: 999, StockCount: 50, internalSKU: "MUG"})
	c.Add(Product{ID: 2, Name: "Book", PriceCent: 1499, StockCount: 30, internalSKU: "BOOK_STD"})

	// What the wire sees on GET /products
	var dtos []ProductDTO
	for _, p := range c.products {
		dtos = append(dtos, toProductDTO(p))
	}
	body, _ := json.MarshalIndent(dtos, "", "  ")
	fmt.Println("GET /products =>")
	fmt.Println(string(body))

	// Decode an incoming POST /orders payload
	raw := `{"items":[{"product_id":1,"quantity":2},{"product_id":2,"quantity":1}]}`
	var req OrderRequestDTO
	_ = json.NewDecoder(strings.NewReader(raw)).Decode(&req)

	resp, err := c.PlaceOrder(req)
	if err != nil {
		fmt.Println("error:", err)
		return
	}
	out, _ := json.MarshalIndent(resp, "", "  ")
	fmt.Println("\nPOST /orders =>")
	fmt.Println(string(out))
}
