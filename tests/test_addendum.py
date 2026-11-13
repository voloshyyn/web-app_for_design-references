"""ADD-001 / SCN-08: authored before rename implementation."""
import json
import pytest
from test_api import api, new_ref


def test_rename_preserves_identity_links_and_persistence(api):
    ref = new_ref(api)
    col = api('POST','/collections',{'name':'Moodboard','description':'Keep me'},201)
    path = '/collections/'+col['id']
    api('POST',path+'/references/'+ref['id'],template='/collections/{id}/references/{ref_id}')
    before = api('GET',path,template='/collections/{id}')
    for _ in range(2):
        assert api('PUT',path,{'name':'Client pitch'},template='/collections/{id}') == {**before,'name':'Client pitch'}
    assert len(api('GET','/collections')) == 1
    from src.api import create_app
    restored = create_app(api.tmp/'catalog.json',api.tmp/'audit.jsonl')
    assert restored.service.collection(col['id']) == {**before,'name':'Client pitch'}
    rows = [json.loads(r) for r in (api.tmp/'audit.jsonl').read_text().splitlines()]
    assert sum(r.get('operation') == 'updateCollection' and r.get('status') == 200 for r in rows) == 2


@pytest.mark.parametrize('body',[{}, {'name':''}, {'name':'   '}, {'name':None}, {'name':12}, {'name':'x'*101}])
def test_rename_invalid_is_atomic(api,body):
    col = api('POST','/collections',{'name':'Before'},201)
    path = '/collections/'+col['id']
    before = api('GET',path,template='/collections/{id}')
    api('PUT',path,body,400,'/collections/{id}')
    assert api('GET',path,template='/collections/{id}') == before


def test_rename_missing_and_max_length(api):
    api('PUT','/collections/missing',{'name':'New'},404,'/collections/{id}')
    col = api('POST','/collections',{'name':'Before'},201)
    result = api('PUT','/collections/'+col['id'],{'name':'x'*100},template='/collections/{id}')
    assert result['name'] == 'x'*100
