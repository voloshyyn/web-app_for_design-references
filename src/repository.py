"""Local JSON persistence. Replacement is atomic; failed saves preserve the old file."""
import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.models import Catalog, Collection, Reference


def reference_dto(ref):
    result = asdict(ref)
    result['tags'] = sorted(ref.tags)
    result['created_at'] = ref.created_at.isoformat()
    return result


class Repository:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        catalog = Catalog()
        descriptions = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding='utf-8'))
            catalog.categories = set(data['categories'])
            for value in data['references']:
                value['created_at'] = datetime.fromisoformat(value['created_at'])
                catalog.add_reference(Reference(**value))
            for value in data['collections']:
                descriptions[value['id']] = value.pop('description', None)
                value['reference_ids'] = set(value['reference_ids'])
                catalog.collections[value['id']] = Collection(**value)
        return catalog, descriptions

    def save(self, catalog, descriptions):
        data = {
            'categories': sorted(catalog.categories),
            'references': [reference_dto(r) for r in catalog.references.values()],
            'collections': [dict(id=c.id, name=c.name, reference_ids=sorted(c.reference_ids),
                                 description=descriptions.get(c.id)) for c in catalog.collections.values()],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with NamedTemporaryFile('w', encoding='utf-8', dir=self.path.parent,
                                    delete=False, suffix='.tmp') as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
