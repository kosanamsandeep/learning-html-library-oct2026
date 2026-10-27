// Notification platform — Go parallel of Python p9.
//
// Lesson: Factory + Strategy via a registry of interface implementations.
// Plus a fan-out using goroutines — the part Python's asyncio would
// usually handle.
package main

import (
	"fmt"
	"sync"
	"time"
)

// Channel is the strategy interface — one method.
type Channel interface {
	Send(to, body string) error
}

// --- concrete strategies ---

type EmailChannel struct{}

func (EmailChannel) Send(to, body string) error {
	time.Sleep(20 * time.Millisecond)
	fmt.Printf("  email -> %s: %s\n", to, body)
	return nil
}

type SMSChannel struct{}

func (SMSChannel) Send(to, body string) error {
	time.Sleep(10 * time.Millisecond)
	fmt.Printf("  sms   -> %s: %s\n", to, body)
	return nil
}

type SlackChannel struct{}

func (SlackChannel) Send(to, body string) error {
	time.Sleep(15 * time.Millisecond)
	fmt.Printf("  slack -> %s: %s\n", to, body)
	return nil
}

// --- registry (the factory) ---

type Registry struct {
	channels map[string]Channel
}

func NewRegistry() *Registry { return &Registry{channels: map[string]Channel{}} }

func (r *Registry) Register(name string, c Channel) { r.channels[name] = c }

func (r *Registry) Get(name string) (Channel, bool) {
	c, ok := r.channels[name]
	return c, ok
}

// --- fan-out send across many channels in parallel using goroutines ---

func (r *Registry) Broadcast(channels []string, to, body string) {
	var wg sync.WaitGroup
	for _, name := range channels {
		c, ok := r.Get(name)
		if !ok {
			fmt.Println("  unknown channel:", name)
			continue
		}
		wg.Add(1)
		// Capture the loop variables — note the explicit copies.
		name, c := name, c
		go func() {
			defer wg.Done()
			if err := c.Send(to, body); err != nil {
				fmt.Printf("  %s failed: %s\n", name, err)
			}
		}()
	}
	wg.Wait()
}

func main() {
	reg := NewRegistry()
	reg.Register("email", EmailChannel{})
	reg.Register("sms", SMSChannel{})
	reg.Register("slack", SlackChannel{})

	fmt.Println("sequential:")
	for _, name := range []string{"email", "sms", "slack"} {
		c, _ := reg.Get(name)
		_ = c.Send("ada@example.com", "hello sequential")
	}

	fmt.Println("\nparallel via goroutines:")
	start := time.Now()
	reg.Broadcast([]string{"email", "sms", "slack", "carrier-pigeon"}, "ada@example.com", "hello parallel")
	fmt.Printf("done in %v\n", time.Since(start))
}
