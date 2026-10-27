// Hospital management — Go parallel of Python p3.
//
// Lesson: composition. A Hospital owns Departments; each Department owns
// Doctors; each Doctor schedules Appointments. In Go, composition is the
// default — you literally put one struct inside another.
package main

import (
	"errors"
	"fmt"
	"time"
)

type Appointment struct {
	PatientName string
	When        time.Time
}

type Doctor struct {
	ID           int
	Name         string
	Specialty    string
	Appointments []Appointment
}

// Pointer receiver — we mutate Appointments.
func (d *Doctor) Book(patient string, when time.Time) {
	d.Appointments = append(d.Appointments, Appointment{patient, when})
}

type Department struct {
	Name    string
	Doctors []*Doctor
}

// FindDoctor returns the doctor and a boolean — Go's "exists?" idiom,
// equivalent to `dict.get(...)` returning Optional in Python.
func (d *Department) FindDoctor(id int) (*Doctor, bool) {
	for _, doc := range d.Doctors {
		if doc.ID == id {
			return doc, true
		}
	}
	return nil, false
}

type Hospital struct {
	Name        string
	Departments map[string]*Department
}

func NewHospital(name string) *Hospital {
	return &Hospital{Name: name, Departments: map[string]*Department{}}
}

func (h *Hospital) AddDepartment(name string) *Department {
	d := &Department{Name: name}
	h.Departments[name] = d
	return d
}

func (h *Hospital) Book(dept string, doctorID int, patient string, when time.Time) error {
	d, ok := h.Departments[dept]
	if !ok {
		return fmt.Errorf("no such department: %s", dept)
	}
	doc, ok := d.FindDoctor(doctorID)
	if !ok {
		return errors.New("no such doctor")
	}
	doc.Book(patient, when)
	return nil
}

func main() {
	h := NewHospital("Mercy General")

	cardio := h.AddDepartment("Cardiology")
	cardio.Doctors = append(cardio.Doctors,
		&Doctor{ID: 1, Name: "Dr. Lin", Specialty: "interventional"},
		&Doctor{ID: 2, Name: "Dr. Patel", Specialty: "imaging"},
	)

	when := time.Date(2026, 6, 15, 9, 30, 0, 0, time.UTC)
	if err := h.Book("Cardiology", 1, "Ada", when); err != nil {
		fmt.Println("error:", err)
	}
	if err := h.Book("Cardiology", 1, "Bob", when.Add(time.Hour)); err != nil {
		fmt.Println("error:", err)
	}
	if err := h.Book("Neurology", 1, "Cy", when); err != nil {
		fmt.Println("expected error:", err)
	}

	fmt.Printf("\n%s\n", h.Name)
	for _, dept := range h.Departments {
		fmt.Printf("  %s\n", dept.Name)
		for _, doc := range dept.Doctors {
			fmt.Printf("    %s (%s) - %d appts\n", doc.Name, doc.Specialty, len(doc.Appointments))
			for _, a := range doc.Appointments {
				fmt.Printf("      %s @ %s\n", a.PatientName, a.When.Format("2006-01-02 15:04"))
			}
		}
	}
}
