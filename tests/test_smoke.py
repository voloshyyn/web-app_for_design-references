"""
Smoke test to verify domain model initialization.
"""
from src.models import Reference

def test_create_reference():
    ref = Reference(
        id="ref-001",
        title="Minimalist Landing Page Design",
        url="https://example.com/inspiration-1"
    )
    assert ref.title == "Minimalist Landing Page Design"
    assert ref.category == "General"
    assert hasattr(ref, "tags")
