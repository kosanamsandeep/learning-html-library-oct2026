// Contact management — Go parallel of Python p5.
//
// Lesson: nested structs + validation. The Python version reaches for
// pydantic for runtime schema; Go gets most of the same payoff at compile
// time because the struct shape *is* the schema, plus a hand-written
// Validate method for cross-field rules.
package main

import (
	"errors"
	"fmt"
	"regexp"
	"strings"
)

type Address struct {
	Line1, City, Country, Postcode string
}

type Phone struct {
	Kind   string // "mobile" | "work" | "home"
	Number string
}

type Email struct {
	Address string
	Primary bool
}

type Contact struct {
	ID        int
	FirstName string
	LastName  string
	Addresses []Address
	Phones    []Phone
	Emails    []Email
}

var emailRe = regexp.MustCompile(`^[^@\s]+@[^@\s]+\.[^@\s]+$`)

// Validate is the Go equivalent of pydantic's __post_init__.
// We collect every error so the caller sees them all in one go.
func (c Contact) Validate() error {
	var errs []string
	if strings.TrimSpace(c.FirstName) == "" {
		errs = append(errs, "first name required")
	}
	if strings.TrimSpace(c.LastName) == "" {
		errs = append(errs, "last name required")
	}
	if len(c.Emails) == 0 {
		errs = append(errs, "at least one email required")
	}

	primaries := 0
	for i, e := range c.Emails {
		if !emailRe.MatchString(e.Address) {
			errs = append(errs, fmt.Sprintf("emails[%d]: invalid format %q", i, e.Address))
		}
		if e.Primary {
			primaries++
		}
	}
	if len(c.Emails) > 0 && primaries != 1 {
		errs = append(errs, fmt.Sprintf("exactly one primary email required, got %d", primaries))
	}

	for i, p := range c.Phones {
		if len(p.Number) < 6 {
			errs = append(errs, fmt.Sprintf("phones[%d]: number too short", i))
		}
		switch p.Kind {
		case "mobile", "work", "home":
		default:
			errs = append(errs, fmt.Sprintf("phones[%d]: bad kind %q", i, p.Kind))
		}
	}

	if len(errs) == 0 {
		return nil
	}
	return errors.New(strings.Join(errs, "; "))
}

func main() {
	good := Contact{
		ID: 1, FirstName: "Ada", LastName: "Lovelace",
		Addresses: []Address{{Line1: "10 King St", City: "London", Country: "UK", Postcode: "SW1"}},
		Phones:    []Phone{{Kind: "mobile", Number: "+447700900123"}},
		Emails:    []Email{{Address: "ada@example.com", Primary: true}},
	}
	bad := Contact{
		ID: 2, FirstName: "", LastName: "Hopper",
		Phones: []Phone{{Kind: "fax", Number: "12"}},
		Emails: []Email{
			{Address: "not-an-email", Primary: true},
			{Address: "h2@example.com", Primary: true}, // 2 primaries
		},
	}

	for _, c := range []Contact{good, bad} {
		if err := c.Validate(); err != nil {
			fmt.Printf("%s %s: INVALID -> %s\n", c.FirstName, c.LastName, err)
		} else {
			fmt.Printf("%s %s: OK\n", c.FirstName, c.LastName)
		}
	}
}
