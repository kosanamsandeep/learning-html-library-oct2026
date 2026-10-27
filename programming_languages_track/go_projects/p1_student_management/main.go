// Student-management demo — the Go parallel of Python p1.
//
// Mirrors the Python service-layer / encapsulation lesson:
//   - Student is a value-type struct.
//   - StudentService holds the in-memory store and exposes operations.
//   - Methods on pointer receivers (*StudentService) so they can mutate state.
package main

import (
	"errors"
	"fmt"
	"sort"
)

// Student is the domain object. Capitalised fields are exported (public).
type Student struct {
	ID    int
	Name  string
	Grade int
}

// String makes Student print nicely with fmt.Println — like __repr__ in Python.
func (s Student) String() string {
	return fmt.Sprintf("Student#%d %s (grade %d)", s.ID, s.Name, s.Grade)
}

// StudentService owns the store. In Python this would be a class with __init__.
type StudentService struct {
	students map[int]Student
	nextID   int
}

func NewStudentService() *StudentService {
	return &StudentService{students: map[int]Student{}, nextID: 1}
}

// Add returns the new student. Note: Go has no exceptions, so we return
// (T, error) and the caller checks err.
func (svc *StudentService) Add(name string, grade int) (Student, error) {
	if name == "" {
		return Student{}, errors.New("name is required")
	}
	s := Student{ID: svc.nextID, Name: name, Grade: grade}
	svc.students[s.ID] = s
	svc.nextID++
	return s, nil
}

func (svc *StudentService) Get(id int) (Student, bool) {
	s, ok := svc.students[id]
	return s, ok
}

// List returns a stable, sorted slice — Python's sorted(list).
func (svc *StudentService) List() []Student {
	out := make([]Student, 0, len(svc.students))
	for _, s := range svc.students {
		out = append(out, s)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out
}

func (svc *StudentService) AverageGrade() float64 {
	if len(svc.students) == 0 {
		return 0
	}
	total := 0
	for _, s := range svc.students {
		total += s.Grade
	}
	return float64(total) / float64(len(svc.students))
}

func main() {
	svc := NewStudentService()

	for _, sample := range []struct {
		name  string
		grade int
	}{{"Ada", 91}, {"Bob", 88}, {"Cy", 79}} {
		if s, err := svc.Add(sample.name, sample.grade); err != nil {
			fmt.Println("error:", err)
		} else {
			fmt.Println("added:", s)
		}
	}

	fmt.Println("\nall students:")
	for _, s := range svc.List() {
		fmt.Println(" ", s)
	}
	fmt.Printf("\naverage grade: %.2f\n", svc.AverageGrade())
}
