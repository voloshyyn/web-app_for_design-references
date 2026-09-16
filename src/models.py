"""
Domain models for Design Reference Catalog System.
Agent variant: Optimized for instant, flat tag-based search.
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
    # AGENT IMPLEMENTATION: Flat set of normalized tags for O(1) instant search lookup
    tags: Set[str] = field(default_factory=set)

    def matches_tag(self, query_tag: str) -> bool:
        """Fast lookup method requested for rapid reference retrieval."""
        return query_tag.strip().lower() in {t.lower() for t in self.tags}
