"""
Domain models for Design Reference Catalog System.
Initial baseline model according to spec/concept.md.
"""
from dataclasses import dataclass, field
from typing import List, Optional
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
    tags: List[str] = field(default_factory=list)
