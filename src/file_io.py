"""Bounded reads shared by entry points and local stores."""
from pathlib import Path
from .food_adapter import ValidationError


def read_text(path: Path, maximum: int = 128000) -> str:
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValidationError(f"Input file exceeds {maximum} bytes.")
    return raw.decode("utf-8")
