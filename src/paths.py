"""Project paths resolve from the installed source, never shell cwd."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
