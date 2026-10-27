// Authentication platform — Go parallel of Python p8.
//
// Lesson: pluggable strategies via interfaces + dependency injection.
// PasswordAuth and APIKeyAuth both implement Authenticator; the AuthService
// holds *whichever* you give it.
package main

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
)

// Identity is what every authenticator returns on success.
type Identity struct {
	UserID int
	Name   string
}

// Authenticator is the contract — one method, one purpose.
type Authenticator interface {
	Authenticate(creds map[string]string) (Identity, error)
}

// --- password strategy ---

type PasswordAuth struct {
	users map[string]string // username -> sha256 hex of password
	ids   map[string]Identity
}

func NewPasswordAuth() *PasswordAuth {
	return &PasswordAuth{users: map[string]string{}, ids: map[string]Identity{}}
}

func hash(pw string) string {
	sum := sha256.Sum256([]byte(pw))
	return hex.EncodeToString(sum[:])
}

func demoCredential(label string) string {
	buf := make([]byte, 8)
	if _, err := rand.Read(buf); err != nil {
		panic(err)
	}
	return fmt.Sprintf("demo-%s-%s", label, hex.EncodeToString(buf))
}

func (a *PasswordAuth) Register(name, pw string, id int) {
	a.users[name] = hash(pw)
	a.ids[name] = Identity{UserID: id, Name: name}
}

func (a *PasswordAuth) Authenticate(creds map[string]string) (Identity, error) {
	got, ok := a.users[creds["username"]]
	if !ok || got != hash(creds["password"]) {
		return Identity{}, errors.New("invalid credentials")
	}
	return a.ids[creds["username"]], nil
}

// --- api-key strategy ---

type APIKeyAuth struct {
	keys map[string]Identity // key -> identity
}

func NewAPIKeyAuth() *APIKeyAuth { return &APIKeyAuth{keys: map[string]Identity{}} }

func (a *APIKeyAuth) Issue(id int, name string) string {
	key := demoCredential("api-key")
	a.keys[key] = Identity{UserID: id, Name: name}
	return key
}

func (a *APIKeyAuth) Authenticate(creds map[string]string) (Identity, error) {
	id, ok := a.keys[creds["api_key"]]
	if !ok {
		return Identity{}, errors.New("unknown api key")
	}
	return id, nil
}

// --- service depending on Authenticator ---

type AuthService struct{ a Authenticator }

func (s *AuthService) Login(creds map[string]string) {
	id, err := s.a.Authenticate(creds)
	if err != nil {
		fmt.Println("DENY:", err)
		return
	}
	fmt.Printf("ALLOW: user_id=%d name=%s\n", id.UserID, id.Name)
}

func main() {
	pw := NewPasswordAuth()
	adaPassword := demoCredential("ada")
	bobPassword := demoCredential("bob")
	pw.Register("ada", adaPassword, 1)
	pw.Register("bob", bobPassword, 2)

	api := NewAPIKeyAuth()
	adaAPIKey := api.Issue(1, "ada")

	pwSvc := &AuthService{a: pw}
	pwSvc.Login(map[string]string{"username": "ada", "password": adaPassword})
	pwSvc.Login(map[string]string{"username": "ada", "password": demoCredential("invalid")})

	apiSvc := &AuthService{a: api}
	apiSvc.Login(map[string]string{"api_key": adaAPIKey})
	apiSvc.Login(map[string]string{"api_key": demoCredential("unknown-api-key")})
}
