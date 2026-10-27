"""
=============================================================================
PROJECT 1: STUDENT MANAGEMENT SYSTEM
=============================================================================
FILE: main.py
PURPOSE: Entry point - demonstrates how the system works end-to-end

WHAT YOU LEARN HERE:
- How all the pieces connect together
- This is the "user interface" (console-based for simplicity)
- In a real app, this would be replaced by a web API or GUI
=============================================================================
"""

from services.student_service import StudentService


def main() -> None:
    """
    Demonstrate the Student Management System.

    FLOW:
    1. Create the service (our "controller")
    2. Add some students
    3. Add grades
    4. Generate reports
    """
    # =========================================================================
    # STEP 1: Create the service
    # =========================================================================
    # The service is our single point of contact for all student operations
    service = StudentService()
    print("=" * 60)
    print("     STUDENT MANAGEMENT SYSTEM - Demo")
    print("=" * 60)

    # =========================================================================
    # STEP 2: Enroll students
    # =========================================================================
    print("\n📝 Enrolling students...")

    alice = service.add_student("S001", "Alice Johnson", 20)
    bob = service.add_student("S002", "Bob Smith", 21)
    charlie = service.add_student("S003", "Charlie Brown", 19)
    diana = service.add_student("S004", "Diana Prince", 22)

    print(f"  Enrolled: {alice}")
    print(f"  Enrolled: {bob}")
    print(f"  Enrolled: {charlie}")
    print(f"  Enrolled: {diana}")
    print(f"  Total students: {service.get_student_count()}")

    # =========================================================================
    # STEP 3: Add grades
    # =========================================================================
    print("\n📊 Adding grades...")

    # Alice - excellent student
    service.add_grade_to_student("S001", 95)
    service.add_grade_to_student("S001", 88)
    service.add_grade_to_student("S001", 92)

    # Bob - average student
    service.add_grade_to_student("S002", 65)
    service.add_grade_to_student("S002", 72)
    service.add_grade_to_student("S002", 58)

    # Charlie - struggling student
    service.add_grade_to_student("S003", 40)
    service.add_grade_to_student("S003", 35)
    service.add_grade_to_student("S003", 45)

    # Diana - good student
    service.add_grade_to_student("S004", 85)
    service.add_grade_to_student("S004", 79)
    service.add_grade_to_student("S004", 90)

    print("  Grades added successfully!")

    # =========================================================================
    # STEP 4: Generate reports
    # =========================================================================
    print("\n📈 Student Report Card:")
    print("-" * 60)

    for student in service.get_all_students():
        status = "✅ PASSING" if student.is_passing() else "❌ FAILING"
        print(f"  {student.name:20} | Avg: {student.get_average():5.1f} | {status}")

    print("-" * 60)
    print(f"  Class Average: {service.get_class_average():.1f}")

    # =========================================================================
    # STEP 5: Top students
    # =========================================================================
    print("\n🏆 Top 3 Students:")
    for i, student in enumerate(service.get_top_students(3), 1):
        print(f"  #{i} {student.name} (Avg: {student.get_average():.1f})")

    # =========================================================================
    # STEP 6: Students needing help
    # =========================================================================
    print("\n⚠️  Students Needing Help (failing):")
    failing = service.get_failing_students()
    if failing:
        for student in failing:
            print(f"  - {student.name} (Avg: {student.get_average():.1f})")
    else:
        print("  None! Everyone is passing!")

    # =========================================================================
    # STEP 7: Demonstrate error handling
    # =========================================================================
    print("\n🔒 Testing Error Handling:")

    # Try to add duplicate student
    try:
        service.add_student("S001", "Fake Alice", 20)
    except ValueError as e:
        print(f"  [CAUGHT] {e}")

    # Try to add invalid grade
    result = alice.add_grade(150)  # Too high!
    print(f"  Adding grade 150: {'Accepted' if result else 'Rejected (as expected)'}")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
