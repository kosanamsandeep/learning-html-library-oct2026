"""
=============================================================================
PROJECT 1: STUDENT MANAGEMENT SYSTEM
=============================================================================
FILE: tests/test_student.py
PURPOSE: Unit tests to verify our Student class works correctly

WHAT YOU LEARN HERE:
- UNIT TESTING verifies each piece works in isolation
- Tests are DOCUMENTATION - they show how code should behave
- Tests give CONFIDENCE to refactor (change without fear of breaking things)
- Each test should test ONE thing (Single Responsibility for tests!)

HOW TO RUN: python -m pytest tests/ -v
=============================================================================
"""

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.student import Student
from services.student_service import StudentService

# =============================================================================
# TESTS FOR STUDENT MODEL
# =============================================================================


class TestStudent:
    """Tests for the Student class (model layer)."""

    def test_create_student(self):
        """Test: Can we create a student with correct attributes?"""
        student = Student(student_id="S001", name="Alice", age=20)

        assert student.student_id == "S001"
        assert student.name == "Alice"
        assert student.age == 20
        assert student.get_grade_count() == 0  # No grades initially

    def test_add_valid_grade(self):
        """Test: Adding a valid grade (0-100) should succeed."""
        student = Student("S001", "Bob", 21)

        result = student.add_grade(85.5)

        assert result is True  # Should return True for valid grade
        assert student.get_grade_count() == 1

    def test_add_invalid_grade_too_high(self):
        """Test: Adding grade > 100 should fail."""
        student = Student("S001", "Charlie", 22)

        result = student.add_grade(150)  # Invalid!

        assert result is False  # Should be rejected
        assert student.get_grade_count() == 0  # Nothing added

    def test_add_invalid_grade_negative(self):
        """Test: Adding negative grade should fail."""
        student = Student("S001", "Diana", 19)

        result = student.add_grade(-10)  # Invalid!

        assert result is False
        assert student.get_grade_count() == 0

    def test_get_average(self):
        """Test: Average calculation with multiple grades."""
        student = Student("S001", "Eve", 20)
        student.add_grade(80)
        student.add_grade(90)
        student.add_grade(70)

        # (80 + 90 + 70) / 3 = 80.0
        assert student.get_average() == 80.0

    def test_get_average_no_grades(self):
        """Test: Average with no grades should return 0 (not crash!)."""
        student = Student("S001", "Frank", 20)

        assert student.get_average() == 0.0  # Safe default

    def test_is_passing_true(self):
        """Test: Student with 80 avg should be passing."""
        student = Student("S001", "Grace", 20)
        student.add_grade(80)

        assert student.is_passing() is True

    def test_is_passing_false(self):
        """Test: Student with 30 avg should be failing."""
        student = Student("S001", "Hank", 20)
        student.add_grade(30)

        assert student.is_passing() is False

    def test_is_passing_custom_threshold(self):
        """Test: Custom passing grade threshold."""
        student = Student("S001", "Iris", 20)
        student.add_grade(55)

        # Default (50) → passing, but with 60 threshold → failing
        assert student.is_passing(50) is True
        assert student.is_passing(60) is False

    def test_str_representation(self):
        """Test: String output is human-readable."""
        student = Student("S001", "Jack", 20)
        student.add_grade(75)

        output = str(student)
        assert "Jack" in output
        assert "S001" in output


# =============================================================================
# TESTS FOR STUDENT SERVICE
# =============================================================================


class TestStudentService:
    """Tests for the StudentService (business logic layer)."""

    def test_add_student(self):
        """Test: Adding a valid student works."""
        service = StudentService()

        student = service.add_student("S001", "Alice", 20)

        assert student.name == "Alice"
        assert service.get_student_count() == 1

    def test_add_duplicate_student_raises_error(self):
        """Test: Can't add two students with same ID."""
        service = StudentService()
        service.add_student("S001", "Alice", 20)

        try:
            service.add_student("S001", "Bob", 21)  # Same ID!
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "already exists" in str(e)

    def test_add_student_invalid_age(self):
        """Test: Age validation works."""
        service = StudentService()

        try:
            service.add_student("S001", "Alice", 3)  # Too young!
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected

    def test_get_student_found(self):
        """Test: Looking up an existing student returns them."""
        service = StudentService()
        service.add_student("S001", "Alice", 20)

        student = service.get_student("S001")

        assert student is not None
        assert student.name == "Alice"

    def test_get_student_not_found(self):
        """Test: Looking up non-existent student returns None."""
        service = StudentService()

        student = service.get_student("FAKE")

        assert student is None

    def test_remove_student(self):
        """Test: Removing a student works."""
        service = StudentService()
        service.add_student("S001", "Alice", 20)

        result = service.remove_student("S001")

        assert result is True
        assert service.get_student_count() == 0

    def test_class_average(self):
        """Test: Class average across multiple students."""
        service = StudentService()
        service.add_student("S001", "Alice", 20)
        service.add_student("S002", "Bob", 21)

        service.add_grade_to_student("S001", 80)
        service.add_grade_to_student("S002", 60)

        # (80 + 60) / 2 = 70.0
        assert service.get_class_average() == 70.0

    def test_get_top_students(self):
        """Test: Top students sorted by average."""
        service = StudentService()
        service.add_student("S001", "Alice", 20)
        service.add_student("S002", "Bob", 21)
        service.add_student("S003", "Charlie", 22)

        service.add_grade_to_student("S001", 90)  # Highest
        service.add_grade_to_student("S002", 70)  # Middle
        service.add_grade_to_student("S003", 80)  # Second

        top = service.get_top_students(2)

        assert len(top) == 2
        assert top[0].name == "Alice"  # 90 avg
        assert top[1].name == "Charlie"  # 80 avg


# =============================================================================
# RUN TESTS
# =============================================================================
if __name__ == "__main__":
    """
    Quick way to run tests without pytest.
    Just run: python tests/test_student.py
    """
    print("Running Student Model tests...")
    t = TestStudent()
    t.test_create_student()
    t.test_add_valid_grade()
    t.test_add_invalid_grade_too_high()
    t.test_add_invalid_grade_negative()
    t.test_get_average()
    t.test_get_average_no_grades()
    t.test_is_passing_true()
    t.test_is_passing_false()
    t.test_is_passing_custom_threshold()
    t.test_str_representation()
    print("✓ All Student Model tests passed!\n")

    print("Running Student Service tests...")
    t2 = TestStudentService()
    t2.test_add_student()
    t2.test_add_duplicate_student_raises_error()
    t2.test_add_student_invalid_age()
    t2.test_get_student_found()
    t2.test_get_student_not_found()
    t2.test_remove_student()
    t2.test_class_average()
    t2.test_get_top_students()
    print("✓ All Student Service tests passed!\n")

    print("🎉 ALL TESTS PASSED!")
