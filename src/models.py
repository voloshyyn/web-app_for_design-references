"""
Domain models for Design Reference Catalog System.
Human variant: Structured hierarchical taxonomy for tags.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
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
    # HUMAN IMPLEMENTATION: Multi-level hierarchical taxonomy dictionary (e.g. {'style': 'minimal', 'palette': 'dark'})
    tags: Dict[str, str] = field(default_factory=dict)

    def get_tag_path(self, namespace: str) -> Optional[str]:
        """Deep hierarchy taxonomy navigation."""
        return self.tags.get(namespace)
