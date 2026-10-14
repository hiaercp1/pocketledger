"""pytest configuration — adds the backend package root to sys.path."""
import sys
import os

# Ensure the backend/ directory is importable without PYTHONPATH being set
# manually (e.g. when running `pytest` from within backend/).
sys.path.insert(0, os.path.dirname(__file__))
