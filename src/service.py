"""Application operations independent of HTTP transport and presentation."""
from copy import deepcopy
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4

from src.models import Reference, Collection
from src.repository import reference_dto
from src.audit import timestamp


class ApiError(Exception):
    def __init__(self, status, code, detail):
        super().__init__(detail)
        self.status, self.code, self.detail = status, code, detail


def invalid(detail):
    raise ApiError(400, 'VALIDATION_FAILED', detail)


def text_field(body, name, maximum=None, required=False, nullable=False):
    if name not in body:
        if required:
            invalid(f'{name} is required.')
        return
    value = body[name]
    if value is None and nullable:
        return
    if not isinstance(value, str):
        invalid(f'{name} must be a string.')
    if required and not value.strip():
        invalid(f'{name} cannot be empty.')
    if maximum and len(value) > maximum:
        invalid(f'{name} exceeds {maximum} characters.')


def validate_reference(body, create):
    text_field(body, 'title', 255, required=create or 'title' in body)
    text_field(body, 'category')
    text_field(body, 'notes')
    for name in (('url', 'image_url') if create else ('image_url',)):
        text_field(body, name, required=name == 'url', nullable=name == 'image_url')
        value = body.get(name)
        if value is None:
            continue
        if not value.strip():
            invalid(f'{name} cannot be empty.')
        if not value.startswith(('http://', 'https://')):
            raise ApiError(422, 'UNSAFE_URL_PROTOCOL', 'Only http:// and https:// are permitted.')
        try:
            parsed = urlsplit(value)
            if not parsed.hostname or any(c.isspace() for c in value):
                invalid(f'{name} must be an absolute HTTP URL.')
            parsed.port
        except ValueError:
            invalid(f'{name} is malformed.')
    if 'tags' in body and (not isinstance(body['tags'], list) or
                           any(not isinstance(t, str) for t in body['tags'])):
        invalid('tags must be an array of strings.')


class Service:
    def __init__(self, repository):
        self.repository = repository
        self.catalog, self.descriptions = repository.load()

    def collection(self, identifier, detailed=True):
        col = self.get(self.catalog.collections, identifier)
        result = dict(id=col.id, name=col.name, description=self.descriptions.get(col.id))
        result.update({'reference_ids': sorted(col.reference_ids)} if detailed else
                      {'reference_count': len(col.reference_ids)})
        return result

    @staticmethod
    def get(mapping, identifier):
        if identifier not in mapping:
            raise ApiError(404, 'RESOURCE_NOT_FOUND', 'Requested resource does not exist.')
        return mapping[identifier]

    def execute(self, operation, params, query, body):
        # Copy-on-write transaction also restores in-memory state on disk errors.
        read_only = operation in {'getHealthStatus','listReferences','getReferenceById',
                                 'listCollections','getCollectionById','listCategories'}
        if read_only:
            return self.dispatch(operation, params, query, body)
        before = deepcopy((self.catalog, self.descriptions))
        try:
            result = self.dispatch(operation, params, query, body)
            self.repository.save(self.catalog, self.descriptions)
            return result
        except Exception:
            self.catalog, self.descriptions = before
            raise

    def dispatch(self, operation, params, query, body):
        cat = self.catalog
        identifier = params.get('id')
        if operation == 'getHealthStatus':
            return 200, dict(status='healthy', version='1.0.0', service='design-reference-catalog-api',
                             timestamp=timestamp(), latency_target_ms=50)
        if operation == 'listReferences':
            try:
                limit, offset = int(query.get('limit','50')), int(query.get('offset','0'))
            except ValueError:
                invalid('limit and offset must be integers.')
            if not 1 <= limit <= 100 or offset < 0:
                invalid('limit must be 1..100; offset must be non-negative.')
            refs = cat.filter_by_tags(set(query.get('tags','').split(',')))
            matches = {r.id for r in cat.search(query.get('q',''))}
            refs = [r for r in refs if r.id in matches and
                    ('category' not in query or r.category == query['category'])]
            return 200, dict(items=[reference_dto(r) for r in refs[offset:offset+limit]],
                             total=len(refs), limit=limit, offset=offset)
        if operation == 'createReference':
            validate_reference(body, True)
            fields = {k: v for k, v in body.items() if k in
                      {'title','url','image_url','category','tags','notes'}}
            ref = Reference(id=uuid4().hex, created_at=datetime.now(timezone.utc), **fields)
            cat.add_reference(ref)
            return 201, reference_dto(ref)
        if operation in {'getReferenceById','updateReference','deleteReference'}:
            ref = self.get(cat.references, identifier)
            if operation == 'deleteReference':
                cat.remove_reference(identifier)
                return 204, None
            if operation == 'updateReference':
                validate_reference(body, False)
                fields = {k: v for k, v in body.items() if k in
                          {'title','image_url','category','tags','notes'}}
                data = vars(ref).copy()
                data.update(fields)
                ref = Reference(**data)
                cat.add_reference(ref)
            return 200, reference_dto(ref)
        if operation == 'listCollections':
            return 200, [self.collection(i, False) for i in cat.collections]
        if operation == 'createCollection':
            text_field(body, 'name', 100, required=True)
            text_field(body, 'description', nullable=True)
            col = Collection(id=uuid4().hex, name=body['name'])
            cat.collections[col.id] = col
            self.descriptions[col.id] = body.get('description')
            return 201, self.collection(col.id, False)
        if operation in {'getCollectionById','deleteCollection','addReferenceToCollection',
                         'removeReferenceFromCollection'}:
            col = self.get(cat.collections, identifier)
            if operation == 'getCollectionById':
                return 200, self.collection(identifier)
            if operation == 'deleteCollection':
                del cat.collections[identifier]
                self.descriptions.pop(identifier, None)
                return 204, None
            ref_id = params['ref_id']
            self.get(cat.references, ref_id)
            if operation == 'addReferenceToCollection':
                col.add_reference(ref_id)
                return 200, self.collection(identifier)
            col.remove_reference(ref_id)
            return 204, None
        if operation == 'listCategories':
            return 200, [dict(name=name, is_default=name == 'General') for name in sorted(cat.categories)]
        if operation == 'createCategory':
            text_field(body, 'name', 50, required=True)
            if body['name'] in cat.categories:
                raise ApiError(400, 'CATEGORY_EXISTS', 'Category already exists.')
            cat.categories.add(body['name'])
            return 201, dict(name=body['name'], is_default=False)
        if operation == 'deleteCategory':
            name = params['name']
            if name == 'General':
                raise ApiError(400, 'PROTECTED_RESOURCE', 'General cannot be deleted.')
            if name not in cat.categories:
                raise ApiError(404, 'CATEGORY_NOT_FOUND', 'Category does not exist.')
            count = sum(r.category == name for r in cat.references.values())
            cat.remove_category(name)
            return 200, dict(message=f"Category '{name}' removed successfully.",
                             reassigned_to='General', affected_references_count=count)
        raise ApiError(404, 'RESOURCE_NOT_FOUND', 'Unknown operation.')
