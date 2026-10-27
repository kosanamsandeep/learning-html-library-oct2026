"""
=============================================================================
PROJECT 1: STUDENT MANAGEMENT SYSTEM
=============================================================================
FILE: models/__init__.py
PURPOSE: Make 'models' a Python package and expose key classes

WHY __init__.py?
- Tells Python "this folder is a package, not just a folder"
- Allows: from models import Student (clean imports)
- Without it: from models.student import Student (ugly, coupled to file names)
=============================================================================
"""

from .student import Student

# __all__ controls what gets imported with "from models import *"
# It's a safety mechanism - only expose what's meant to be public
__all__ = ["Student"]
