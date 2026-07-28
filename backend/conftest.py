# conftest.py — makes the backend/ directory importable as the project root
import sys
import os

# Ensure `app` can be imported when running pytest from the backend/ directory
sys.path.insert(0, os.path.dirname(__file__))
