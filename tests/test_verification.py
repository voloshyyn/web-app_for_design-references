"""Independent contract invariants, fault injection, model rules and realistic SLA sample."""
import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from openapi_spec_validator import validate
from src.models import Catalog, Reference, ValidationError
from src.repository import Repository
from test_api import api, new_ref


def test_openapi_valid_and_backwards_compatible():
    current = json.loads(Path('spec/openapi.json').read_text(encoding='utf-8'))
    baseline = json.loads(Path('spec/openapi-baseline.json').read_text(encoding='utf-8'))
    assert yaml.safe_load(Path('spec/openapi.yaml').read_text(encoding='utf-8')) == current
    validate(current)
    validate(baseline)
    for path, methods in baseline['paths'].items():
        for method, value in methods.items():
            assert current['paths'][path][method] == value
    for name, schema in baseline['components']['schemas'].items():
        assert current['components']['schemas'][name] == schema


def test_model_rules():
    ref = Reference(id='r',title='X',url='https://example.org',tags={'style:clean'})
    ref.add_tag(' #DARK ')
    ref.add_tag(' ')
    assert ref.matches_tag('#dark') and ref.has_facet('STYLE')
    assert not ref.has_facet('unknown')
    ref.remove_tag('#dark')
    assert not ref.matches_tag('dark')
    catalog = Catalog()
    catalog.add_reference(ref)
    assert catalog.filter_by_tags({' '}) == [ref]
    assert catalog.search(' ') == [ref]
    assert catalog.search('clean') == [ref]
    assert catalog.remove_reference('missing') is None
    catalog.remove_category('General')
    assert 'General' in catalog.categories
    with pytest.raises(ValidationError):
        Reference(id='bad', title='X', url='https://example.org', image_url='data:x')


def test_sla_1000_references():
    catalog = Catalog()
    for i in range(1000):
        catalog.add_reference(Reference(id=str(i),title=f'Design {i}',url='https://example.org',
                                        tags={'mobile','dark','style:clean'} if i % 2 == 0 else {'light'}))
    timings = {}
    for name, action, expected in [
        ('filter',lambda:catalog.filter_by_tags({'mobile','dark','style:clean'}),500),
        ('search',lambda:catalog.search('Design'),1000)]:
        samples = []
        for _ in range(20):
            start = time.perf_counter()
            assert len(action()) == expected
            samples.append((time.perf_counter()-start)*1000)
        timings[name] = {'max_ms':max(samples),'mean_ms':sum(samples)/len(samples)}
        assert max(samples) < 50
    Path('logs/lab5-performance.json').write_text(json.dumps(timings,indent=2),encoding='utf-8')


def test_save_failure_rollback_and_error_log(api):
    ref = new_ref(api)
    previous = (api.tmp/'catalog.json').read_bytes()
    with patch('src.repository.os.replace', side_effect=OSError('private path')):
        result = api('PUT','/references/'+ref['id'],{'title':'Not saved'},500,'/references/{id}')
    assert result['code'] == 'INTERNAL_ERROR' and 'private path' not in str(result)
    assert (api.tmp/'catalog.json').read_bytes() == previous
    assert api('GET','/references/'+ref['id'],template='/references/{id}') == ref
    assert not list(api.tmp.glob('*.tmp'))
    rows = [json.loads(r) for r in (api.tmp/'audit.jsonl').read_text().splitlines()]
    assert any(r['event']=='error' and r['error_type']=='OSError' for r in rows)


def test_restart_preserves_collections_categories(api):
    api('POST','/categories',{'name':'Saved'},201)
    ref = new_ref(api,category='Saved')
    col = api('POST','/collections',{'name':'Saved board','description':'Description'},201)
    api('POST','/collections/'+col['id']+'/references/'+ref['id'],template='/collections/{id}/references/{ref_id}')
    catalog, descriptions = Repository(api.tmp/'catalog.json').load()
    assert 'Saved' in catalog.categories
    assert catalog.collections[col['id']].reference_ids == {ref['id']}
    assert descriptions[col['id']] == 'Description'


def test_corrupt_store_fails_without_overwrite(tmp_path):
    path = tmp_path/'catalog.json'
    path.write_text('{broken',encoding='utf-8')
    with pytest.raises(ValueError):
        Repository(path).load()
    assert path.read_text() == '{broken'
