"""
Automated BDD test suite verifying scenarios defined in spec/bdd-scenarios.md.
Traceability Matrix Reference: spec/traceability-matrix.md
"""
import pytest
import time
from src.models import Reference, Collection, Catalog, ValidationError


def test_scn_01_create_valid_reference():
    """
    Scenario SCN-01: User saves a valid reference with category, tags, and notes.
    Maps to: REQ-F-001, REQ-F-002, REQ-F-004.
    """
    catalog = Catalog()
    ref = Reference(
        id="ref-001",
        title="Dark Minimalist Dashboard",
        url="https://dribbble.com/shots/example-dash",
        image_url="https://cdn.dribbble.com/preview.png",
        category="UI/UX",
        notes="Звернути увагу на відступи карток та контраст шрифтів",
        tags={"#dashboard", "minimalism", "style:dark"}
    )
    catalog.add_reference(ref)

    assert ref.id in catalog.references
    saved = catalog.references["ref-001"]
    assert saved.title == "Dark Minimalist Dashboard"
    assert saved.category == "UI/UX"
    # Verify tag normalization (strip '#' and lowercase)
    assert saved.tags == {"dashboard", "minimalism", "style:dark"}
    assert saved.has_facet("style", "dark")


def test_scn_02_reject_invalid_or_unsafe_url():
    """
    Scenario SCN-02: Rejection of invalid, empty, or malicious URLs.
    Maps to: REQ-F-001, REQ-NF-004 (AC-F-001.2, AC-NF-004.1).
    """
    unsafe_urls = [
        "javascript:alert('XSS')",
        "data:text/html,<script>bad()</script>",
        "ftp://files.example.com/mockup.png",
        "invalid-url-string",
        "",
        "   "
    ]

    for bad_url in unsafe_urls:
        with pytest.raises(ValidationError):
            Reference(
                id="ref-bad",
                title="Suspicious Reference",
                url=bad_url
            )

    # Empty title should also be rejected
    with pytest.raises(ValidationError):
        Reference(
            id="ref-empty-title",
            title="   ",
            url="https://valid-url.com"
        )


def test_scn_03_conjunctive_tag_filtering_and_latency():
    """
    Scenario SCN-03: Multi-tag conjunctive filtering (AND semantics) and latency SLA.
    Maps to: REQ-F-005, REQ-NF-001 (AC-F-005.1, AC-NF-001.1).
    """
    catalog = Catalog()
    r1 = Reference(id="r1", title="Mobile FinTech", url="https://a.com", category="UI/UX", tags={"mobile", "fintech", "dark"})
    r2 = Reference(id="r2", title="Web Crypto Portal", url="https://b.com", category="UI/UX", tags={"web", "fintech", "light"})
    r3 = Reference(id="r3", title="Mobile Game UI", url="https://c.com", category="UI/UX", tags={"mobile", "gamedev", "dark"})
    r4 = Reference(id="r4", title="Branding Identity", url="https://d.com", category="Branding", tags={"minimalism", "print"})

    for r in [r1, r2, r3, r4]:
        catalog.add_reference(r)

    # Benchmark filtering latency
    start = time.perf_counter()
    results = catalog.filter_by_tags({"mobile", "dark"})
    elapsed_ms = (time.perf_counter() - start) * 1000

    result_ids = {r.id for r in results}
    assert result_ids == {"r1", "r3"}
    assert "r2" not in result_ids
    assert "r4" not in result_ids
    # Verify SLA requirement: < 50ms (REQ-NF-001)
    assert elapsed_ms < 50.0


def test_scn_04_faceted_search():
    """
    Scenario SCN-04: Parametric facet filtering by namespace:value prefix.
    Maps to: REQ-F-004, REQ-F-005 (AC-F-004.2, AC-F-005.2).
    """
    catalog = Catalog()
    r1 = Reference(id="r1", title="Cyberpunk HUD", url="https://hud.com", tags={"style:cyberpunk", "theme:dark"})
    r2 = Reference(id="r2", title="Brutalist Blog", url="https://brutal.com", tags={"style:brutalism", "theme:light"})
    r3 = Reference(id="r3", title="Clean Portfolio", url="https://port.com", tags={"style:minimalism", "theme:light"})

    for r in [r1, r2, r3]:
        catalog.add_reference(r)

    # Filter specifically for style:brutalism
    results = catalog.filter_by_tags({"style:brutalism"})
    assert len(results) == 1
    assert results[0].id == "r2"
    assert results[0].has_facet("style", "brutalism")
    assert not results[0].has_facet("style", "minimalism")


def test_scn_05_category_deletion_fallback():
    """
    Scenario SCN-05: Category removal safely reassigns references to 'General' (0% data loss).
    Maps to: REQ-F-002, REQ-F-008, REQ-NF-003 (AC-NF-003.1).
    """
    catalog = Catalog()
    ref = Reference(
        id="ref-render",
        title="Sci-Fi Helmet Render",
        url="https://artstation.com/helmet",
        category="3D",
        tags={"3d", "scifi", "render"},
        notes="Textures in 4K"
    )
    catalog.add_reference(ref)
    assert catalog.references["ref-render"].category == "3D"

    # Remove the category
    catalog.remove_category("3D")

    assert "3D" not in catalog.categories
    # Reference MUST NOT be lost, must fallback to General
    reassigned = catalog.references["ref-render"]
    assert reassigned.category == "General"
    assert reassigned.tags == {"3d", "scifi", "render"}
    assert reassigned.notes == "Textures in 4K"


def test_scn_06_full_text_search():
    """
    Scenario SCN-06: Case-insensitive search across title, notes, and tags.
    Maps to: REQ-F-006 (AC-F-006.1).
    """
    catalog = Catalog()
    ref = Reference(
        id="ref-saas",
        title="SaaS Pricing Page",
        url="https://example.com/pricing",
        notes="Цікава неоморфна тінь на перемикачі місячного тарифу",
        tags={"saas", "pricing", "neomorphism"}
    )
    catalog.add_reference(ref)

    # Search by keyword in notes
    results = catalog.search("неоморфна тінь")
    assert len(results) == 1
    assert results[0].id == "ref-saas"

    # Search case-insensitively by title substring
    results_title = catalog.search("pricing page")
    assert len(results_title) == 1
    assert results_title[0].id == "ref-saas"


def test_scn_07_collection_management():
    """
    Scenario SCN-07: Managing references across multiple collections (M:N).
    Maps to: REQ-F-003, REQ-F-008.
    """
    catalog = Catalog()
    ref = Reference(id="r1", title="Mobile Login Screen", url="https://auth.com")
    catalog.add_reference(ref)

    col1 = Collection(id="c1", name="Fintech App 2026")
    col2 = Collection(id="c2", name="Best Auth Patterns")

    col1.add_reference("r1")
    col2.add_reference("r1")

    catalog.collections["c1"] = col1
    catalog.collections["c2"] = col2

    assert "r1" in col1.reference_ids
    assert "r1" in col2.reference_ids

    # Deleting reference removes it cleanly from collections
    catalog.remove_reference("r1")
    assert "r1" not in catalog.references
    assert "r1" not in col1.reference_ids
    assert "r1" not in col2.reference_ids
