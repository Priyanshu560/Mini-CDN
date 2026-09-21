import os
import sys

# The project uses flat top-level modules (no src/ package layout), so
# tests need the project root on sys.path to import them regardless of
# where `python -m unittest discover` gets invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
