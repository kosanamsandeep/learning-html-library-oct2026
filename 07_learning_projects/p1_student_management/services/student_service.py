"""
=============================================================================
PROJECT 1: STUDENT MANAGEMENT SYSTEM
=============================================================================
FILE: services/student_service.py
PURPOSE: Business logic layer - WHAT operations can we perform on students?

WHAT YOU LEARN HERE:
- SERVICE LAYER separates "business rules" from "data storage"
- The service ORCHESTRATES operations (add student, find student, etc.)
- It doesn't know HOW data is stored (file? database? cloud?)

WHY THIS FILE EXISTS (vs putting logic in Student class):
- Student class knows about ONE student
- StudentService knows about managing MANY students
- This is SEPARATION OF CONCERNS
- If Student class did everything, it would become a "God Object" (anti-pattern)

ARCHITECT THINKING:
- What if we need to add email notifications when a student is added?
  → We add it HERE in the service, not in the Student model
- What if we need to validate business rules (max 30 students per class)?
  → We add it HERE, not in the Student model
=============================================================================
"""

from models.student import Student


class StudentService:
    """
    Manages a collection of students and provides business operations.

    RESPONSIBILITY: Business logic and orchestration
    NOT RESPONSIBLE FOR: Data persistence (that's for repositories - Project 6!)

    Think of this as a SCHOOL ADMINISTRATOR:
    - Can enroll students
    - Can look up students
    - Can generate reports
    - But doesn't personally file paperwork (that's the repository's job)
    """

    def __init__(self) -> None:
        """
        Initialize with an empty collection of students.

        WHY A DICTIONARY?
        - O(1) lookup by student_id (instant, regardless of how many students)
        - A list would require O(n) search (slower as students grow)
        - Key = student_id, Value = Student object
        """
        self._students: dict[str, Student] = {}

    def add_student(self, student_id: str, name: str, age: int) -> Student:
        """
        Enroll a new student in the system.

        BUSINESS RULES:
        1. student_id must be unique (can't have duplicates)
        2. Age must be reasonable (5-100)
        3. Name must not be empty

        WHY RAISE EXCEPTIONS?
        - The caller (UI/API) decides how to handle errors
        - Maybe show an alert, maybe log it, maybe retry
        - The service just enforces rules
        """
        # VALIDATION - enforcing business rules
        if not name or not name.strip():
            raise ValueError("Student name cannot be empty")

        if not 5 <= age <= 100:
            raise ValueError(f"Invalid age: {age}. Must be between 5 and 100")

        if student_id in self._students:
            raise ValueError(f"Student ID '{student_id}' already exists")

        # CREATE the student object
        student = Student(student_id=student_id, name=name.strip(), age=age)

        # STORE it in our collection
        self._students[student_id] = student

        return student

    def get_student(self, student_id: str) -> Student | None:
        """
        Find a student by their ID.

        WHY RETURN None INSTEAD OF RAISING EXCEPTION?
        - "Not found" is a normal scenario, not an error
        - Exceptions are for EXCEPTIONAL situations
        - The caller can check: if student is None: ...
        """
        return self._students.get(student_id)

    def get_all_students(self) -> list[Student]:
        """
        Get all students as a list.

        WHY RETURN A LIST (not the dict)?
        - Hides internal implementation (maybe we switch to a database later)
        - Prevents external code from modifying our internal dict
        - Clean interface - callers don't need to know about our storage
        """
        return list(self._students.values())

    def remove_student(self, student_id: str) -> bool:
        """
        Remove a student from the system.

        Returns True if removed, False if student wasn't found.
        """
        if student_id in self._students:
            del self._students[student_id]
            return True
        return False

    def add_grade_to_student(self, student_id: str, grade: float) -> bool:
        """
        Add a grade to a specific student.

        WHY GO THROUGH THE SERVICE?
        - We might need to log this action
        - We might need to check permissions
        - We might need to send notifications
        - The service is the CONTROL POINT for all operations
        """
        student = self.get_student(student_id)
        if student is None:
            raise ValueError(f"Student '{student_id}' not found")

        return student.add_grade(grade)

    def get_top_students(self, count: int = 5) -> list[Student]:
        """
        Get the top N students by average grade.

        BUSINESS LOGIC: Sorting and filtering belongs in the service,
        not in the model (Student doesn't know about other students).
        """
        students_with_grades = [
            s for s in self._students.values() if s.get_grade_count() > 0
        ]

        # Sort by average (highest first)
        students_with_grades.sort(key=lambda s: s.get_average(), reverse=True)

        return students_with_grades[:count]

    def get_failing_students(self, passing_grade: float = 50.0) -> list[Student]:
        """Get all students who are currently failing."""
        return [
            s
            for s in self._students.values()
            if s.get_grade_count() > 0 and not s.is_passing(passing_grade)
        ]

    def get_class_average(self) -> float:
        """Calculate the average grade across ALL students."""
        students_with_grades = [
            s for s in self._students.values() if s.get_grade_count() > 0
        ]

        if not students_with_grades:
            return 0.0

        total = sum(s.get_average() for s in students_with_grades)
        return total / len(students_with_grades)

    def get_student_count(self) -> int:
        """Return total number of enrolled students."""
        return len(self._students)
