"""
Domain models for Design Reference Catalog System.
SPEC-GATE Approved Baseline v1.0 (Harmonized with IEEE 830 SRS).
Traceability IDs: REQ-F-001 through REQ-F-008, REQ-NF-001 through REQ-NF-005.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict
from datetime import datetime
import re


class ValidationError(ValueError):
    """Raised when domain constraints or security rules are violated."""
    pass


@dataclass
class Reference:
    """
    Domain entity representing a saved visual design reference.
    Maps to REQ-F-001, REQ-F-002, REQ-F-004.
    """
    id: str
    title: str
    url: str
    image_url: Optional[str] = None
    category: str = "General"
    created_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
    # Set of normalized tags (supports both flat tags and facet prefixes 'namespace:value')
    tags: Set[str] = field(default_factory=set)

    def __post_init__(self):
        self.validate()
        # Ensure all initial tags are normalized
        self.tags = {self._normalize_tag(t) for t in self.tags if t and t.strip()}

    @staticmethod
    def _normalize_tag(tag: str) -> str:
        """Normalizes tag to lowercase, stripped without leading '#'."""
        tag = tag.strip().lower()
        if tag.startswith("#"):
            tag = tag[1:]
        return tag

    def validate(self):
        """
        Validates integrity and security constraints (REQ-NF-004, AC-F-001.2, AC-NF-004.1).
        Rejects empty titles, empty URLs, and unsafe protocols (javascript:, data:).
        """
        if not self.title or not self.title.strip():
            raise ValidationError("Title cannot be empty.")
        
        if not self.url or not self.url.strip():
            raise ValidationError("URL cannot be empty.")
        
        url_lower = self.url.strip().lower()
        if not (url_lower.startswith("http://") or url_lower.startswith("https://")):
            raise ValidationError("Invalid URL scheme. Only 'http://' and 'https://' are permitted.")
        
        if self.image_url:
            img_lower = self.image_url.strip().lower()
            if not (img_lower.startswith("http://") or img_lower.startswith("https://")):
                raise ValidationError("Invalid Image URL scheme. Only 'http://' and 'https://' are permitted.")

    def add_tag(self, tag: str) -> None:
        """Adds a normalized tag or facet (REQ-F-004, AC-F-004.1)."""
        normalized = self._normalize_tag(tag)
        if normalized:
            self.tags.add(normalized)

    def remove_tag(self, tag: str) -> None:
        """Removes a tag if present."""
        normalized = self._normalize_tag(tag)
        self.tags.discard(normalized)

    def matches_tag(self, query_tag: str) -> bool:
        """
        Fast lookup method with O(1) set complexity.
        Supports both direct match and facet matching.
        """
        query = self._normalize_tag(query_tag)
        return query in self.tags

    def has_facet(self, namespace: str, value: Optional[str] = None) -> bool:
        """
        Checks if the reference contains a facet tag matching the given namespace (and optional value).
        Example: has_facet("style", "minimalism") matches 'style:minimalism'.
        """
        ns = namespace.strip().lower()
        if value is None:
            prefix = f"{ns}:"
            return any(t.startswith(prefix) for t in self.tags)
        
        target = f"{ns}:{value.strip().lower()}"
        return target in self.tags


@dataclass
class Collection:
    """
    Project board grouping references for a specific project/client (REQ-F-003).
    Many-to-Many relation with Reference.
    """
    id: str
    name: str
    reference_ids: Set[str] = field(default_factory=set)

    def add_reference(self, ref_id: str) -> None:
        self.reference_ids.add(ref_id)

    def remove_reference(self, ref_id: str) -> None:
        self.reference_ids.discard(ref_id)


class Catalog:
    """
    In-memory catalog manager implementing high-performance search and filtering.
    Traceability IDs: REQ-F-005, REQ-F-006, REQ-NF-001, REQ-NF-003.
    """
    def __init__(self):
        self.references: Dict[str, Reference] = {}
        self.collections: Dict[str, Collection] = {}
        self.categories: Set[str] = {"General", "UI/UX", "Branding", "3D", "Typography", "Motion"}

    def add_reference(self, ref: Reference) -> None:
        """Adds or updates a reference in the catalog."""
        ref.validate()
        self.references[ref.id] = ref
        if ref.category not in self.categories:
            self.categories.add(ref.category)

    def remove_reference(self, ref_id: str) -> Optional[Reference]:
        """Removes reference and cleans up references from collections (REQ-F-008)."""
        ref = self.references.pop(ref_id, None)
        if ref:
            for col in self.collections.values():
                col.remove_reference(ref_id)
        return ref

    def filter_by_tags(self, tags: Set[str]) -> List[Reference]:
        """
        Conjunctive filtering (AND semantics) (REQ-F-005, AC-F-005.1).
        Returns only references that contain ALL specified query tags.
        """
        if not tags:
            return list(self.references.values())
        
        normalized_query = {Reference._normalize_tag(t) for t in tags if t.strip()}
        if not normalized_query:
            return list(self.references.values())

        return [
            ref for ref in self.references.values()
            if normalized_query.issubset(ref.tags)
        ]

    def search(self, query: str) -> List[Reference]:
        """
        Case-insensitive full-text search across title, notes, and tags (REQ-F-006, AC-F-006.1).
        """
        q = query.strip().lower()
        if not q:
            return list(self.references.values())

        results = []
        for ref in self.references.values():
            if (q in ref.title.lower() or 
                q in ref.notes.lower() or 
                any(q in t for t in ref.tags)):
                results.append(ref)
        return results

    def remove_category(self, category_name: str) -> None:
        """
        Removes category with fallback reassignment to 'General' (REQ-NF-003, AC-NF-003.1).
        Guarantees 0% data loss.
        """
        if category_name == "General":
            return  # Default system category cannot be deleted
        
        self.categories.discard(category_name)
        for ref in self.references.values():
            if ref.category == category_name:
                ref.category = "General"
