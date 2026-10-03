"""
Smoke test to verify domain model initialization and basic integrity.
"""
from src.models import Reference, Catalog

def test_create_reference():
    ref = Reference(
        id="ref-001",
        title="Minimalist Landing Page Design",
        url="https://example.com/inspiration-1"
    )
    assert ref.title == "Minimalist Landing Page Design"
    assert ref.category == "General"
    assert hasattr(ref, "tags")

def test_catalog_initialization():
    catalog = Catalog()
    assert "General" in catalog.categories
    assert len(catalog.references) == 0
