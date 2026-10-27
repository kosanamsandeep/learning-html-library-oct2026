"""
=============================================================================
PROJECT 1: STUDENT MANAGEMENT SYSTEM
=============================================================================
FILE: models/student.py
PURPOSE: Define the Student class - the core domain object

WHAT YOU LEARN HERE:
- A CLASS is a blueprint (like an architect's drawing)
- An OBJECT is a real instance (like an actual building)
- ENCAPSULATION means hiding internal details and exposing only what's needed
- CONSTRUCTORS (__init__) set up the initial state of an object
- METHODS are behaviors/actions an object can perform

WHY THIS FILE EXISTS:
- Separates the "what is a student?" from "what do we do with students?"
- If we put everything in one file, changes ripple everywhere
- This is the SINGLE RESPONSIBILITY PRINCIPLE (SRP) in action
=============================================================================
"""


class Student:
    """
    Represents a single student in our system.

    Think of this class as a FORM/TEMPLATE:
    - Every student has a name, age, student_id, and grades
    - Every student can calculate their average, check if passing, etc.

    ENCAPSULATION IN ACTION:
    - We use a leading underscore (_grades) to signal "don't touch this directly"
    - We provide methods (add_grade, get_average) as the "official" way to interact
    - This protects data integrity (no one can secretly add invalid grades)
    """

    def __init__(self, student_id: str, name: str, age: int) -> None:
        """
        CONSTRUCTOR - runs automatically when you create a Student object.

        Think of it as filling out a registration form:
        - student_id: unique identifier (like a roll number)
        - name: the student's full name
        - age: the student's age

        WHY TYPE HINTS (str, int, -> None)?
        - They make code self-documenting
        - IDEs can catch errors before runtime
        - Other developers know exactly what to pass in
        """
        # PUBLIC attributes - can be accessed directly
        self.student_id: str = student_id  # Unique identifier
        self.name: str = name  # Student's full name
        self.age: int = age  # Student's age

        # PRIVATE attribute (by convention) - use methods to interact
        # WHY private? Because we want to VALIDATE grades before adding them
        self._grades: list[float] = []  # List of grades (0-100)

    def add_grade(self, grade: float) -> bool:
        """
        Add a grade to the student's record.

        WHY A METHOD INSTEAD OF DIRECT ACCESS?
        - We can VALIDATE: reject grades below 0 or above 100
        - We can LOG: track when grades were added
        - We can NOTIFY: trigger alerts if grade is very low

        Returns True if grade was added, False if invalid.
        """
        # VALIDATION - protecting data integrity
        if not 0 <= grade <= 100:
            return False  # Reject invalid grades

        self._grades.append(grade)
        return True

    def get_average(self) -> float:
        """
        Calculate the average of all grades.

        WHY A METHOD?
        - The average is COMPUTED, not stored
        - If we stored it, it could become stale/incorrect
        - Computing on-demand guarantees accuracy
        """
        if not self._grades:
            return 0.0  # Avoid division by zero

        return sum(self._grades) / len(self._grades)

    def is_passing(self, passing_grade: float = 50.0) -> bool:
        """
        Check if student is passing (average >= passing_grade).

        WHY DEFAULT PARAMETER?
        - Most systems use 50 as passing, but some use 60 or 40
        - Default parameter makes the common case easy
        - But allows flexibility when needed
        """
        return self.get_average() >= passing_grade

    def get_grade_count(self) -> int:
        """Return the number of grades recorded."""
        return len(self._grades)

    def get_highest_grade(self) -> float:
        """Return the highest grade, or 0 if no grades exist."""
        if not self._grades:
            return 0.0
        return max(self._grades)

    def get_lowest_grade(self) -> float:
        """Return the lowest grade, or 0 if no grades exist."""
        if not self._grades:
            return 0.0
        return min(self._grades)

    def __str__(self) -> str:
        """
        Human-readable string representation.

        WHY __str__?
        - Called automatically by print() and str()
        - Makes debugging easier
        - Shows meaningful info instead of <Student object at 0x...>
        """
        return (
            f"Student(id={self.student_id}, name={self.name}, "
            f"age={self.age}, avg={self.get_average():.1f})"
        )

    def __repr__(self) -> str:
        """
        Developer-friendly representation (for debugging).

        WHY __repr__?
        - Used in debugger, logging, and interactive console
        - Should ideally be valid Python to recreate the object
        """
        return f"Student(student_id='{self.student_id}', name='{self.name}', age={self.age})"
