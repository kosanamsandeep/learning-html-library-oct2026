// Banking demo — Go parallel of Python p2.
//
// Python uses class inheritance: SavingsAccount(Account), CheckingAccount(Account).
// Go has *no* inheritance. Instead we use:
//   1. An interface (Account) declaring the behaviour every account type shares.
//   2. Struct embedding (BaseAccount inside SavingsAccount) for code reuse.
package main

import (
	"errors"
	"fmt"
)

// Account is the contract every concrete account satisfies. Tiny interfaces
// (1-3 methods) are idiomatic in Go.
type Account interface {
	Deposit(amount int) error
	Withdraw(amount int) error
	Balance() int
	Type() string
}

// BaseAccount holds the shared fields. Embedding it inside other structs
// gives them all of its fields and methods automatically.
type BaseAccount struct {
	Holder      string
	balanceCent int
}

func (a *BaseAccount) Deposit(amount int) error {
	if amount <= 0 {
		return errors.New("deposit must be positive")
	}
	a.balanceCent += amount
	return nil
}

func (a *BaseAccount) Balance() int { return a.balanceCent }

// --- Savings: 5% bonus on every deposit ---

type SavingsAccount struct {
	BaseAccount
}

func (a *SavingsAccount) Deposit(amount int) error {
	if amount <= 0 {
		return errors.New("deposit must be positive")
	}
	a.balanceCent += amount + amount/20 // 5% bonus
	return nil
}

func (a *SavingsAccount) Withdraw(amount int) error {
	if amount > a.balanceCent {
		return errors.New("insufficient funds")
	}
	a.balanceCent -= amount
	return nil
}

func (a *SavingsAccount) Type() string { return "savings" }

// --- Checking: allows overdraft up to a limit ---

type CheckingAccount struct {
	BaseAccount
	overdraftCent int
}

func (a *CheckingAccount) Withdraw(amount int) error {
	if amount > a.balanceCent+a.overdraftCent {
		return errors.New("over overdraft limit")
	}
	a.balanceCent -= amount
	return nil
}

func (a *CheckingAccount) Type() string { return "checking" }

// summarise works on *any* Account — that's polymorphism without inheritance.
func summarise(accounts []Account) {
	for _, a := range accounts {
		fmt.Printf("  %-9s holder=%s balance=%d cents\n",
			a.Type(), holderOf(a), a.Balance())
	}
}

func holderOf(a Account) string {
	switch v := a.(type) {
	case *SavingsAccount:
		return v.Holder
	case *CheckingAccount:
		return v.Holder
	default:
		return "?"
	}
}

func main() {
	savings := &SavingsAccount{BaseAccount: BaseAccount{Holder: "Ada"}}
	checking := &CheckingAccount{BaseAccount: BaseAccount{Holder: "Bob"}, overdraftCent: 5000}

	_ = savings.Deposit(10_000)  // 10500 after 5% bonus
	_ = checking.Deposit(2_000)
	_ = checking.Withdraw(6_000) // dips into overdraft

	if err := checking.Withdraw(99_999); err != nil {
		fmt.Println("declined:", err)
	}

	summarise([]Account{savings, checking})
}
