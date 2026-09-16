"""
Domain models for Design Reference Catalog System.
GIT-GATE Resolution: Harmonized model based on spec/concept.md (priority: fast search & simple tagging).
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set
from datetime import datetime

@dataclass
class Reference:
    id: str
    title: str
    url: str
    image_url: Optional[str] = None
    category: str = "General"
    created_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
    # RESOLVED VIA GIT-GATE: Flat set of tags prioritized for rapid cross-filtering (FR-4)
    # Advanced hierarchical taxonomy deferred to Lab 2 SRS specification analysis.
    tags: Set[str] = field(default_factory=set)

    def matches_tag(self, query_tag: str) -> bool:
        """Fast lookup method for rapid designer workflow."""
        return query_tag.strip().lower() in {t.lower() for t in self.tags}
