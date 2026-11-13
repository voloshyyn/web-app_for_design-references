"""HTTP acceptance tests derived from SRS v1.0 and approved OpenAPI, before API code."""
import json
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from wsgiref.simple_server import make_server, WSGIRequestHandler

import pytest
from jsonschema import Draft4Validator, FormatChecker

SPEC = json.load(open('spec/openapi.json', encoding='utf-8'))


def resolve(value):
    if isinstance(value, dict):
        if '$ref' in value:
            target = SPEC
            for part in value['$ref'].split('/')[1:]:
                target = target[part]
            return resolve(target)
        value = {k: resolve(v) for k, v in value.items()}
        if value.pop('nullable', False) and 'type' in value:
            value['type'] = [value['type'], 'null']
        return value
    return [resolve(v) for v in value] if isinstance(value, list) else value


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def api(tmp_path):
    from src.api import create_app
    app = create_app(tmp_path / 'catalog.json', tmp_path / 'audit.jsonl')
    server = make_server('127.0.0.1', 0, app, handler_class=QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def call(method, path, body=None, status=200, template=None, raw=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = Request(f'http://127.0.0.1:{server.server_port}/api/v1{path}',
                      data=data, method=method, headers={'Content-Type': 'application/json'})
        try:
            response = urlopen(req)
        except HTTPError as error:
            response = error
        with response:
            payload = response.read()
            assert response.status == status, payload
            if status == 204:
                assert payload == b''
                return None
            result = json.loads(payload)
            media = 'application/problem+json' if status >= 400 else 'application/json'
            assert response.headers['Content-Type'].startswith(media)
            contract_path = template or path.split('?')[0]
            schema = resolve(SPEC['paths'][contract_path][method.lower()]['responses'][str(status)])['content'][media]['schema']
            Draft4Validator(schema, format_checker=FormatChecker()).validate(result)
            return result

    call.app = app
    call.tmp = tmp_path
    yield call
    server.shutdown()
    server.server_close()
    thread.join()


def new_ref(api, **fields):
    return api('POST', '/references', {'title': 'Dashboard', 'url': 'https://example.org', **fields}, 201)


def test_reference_lifecycle(api):
    """REQ-F-001/002/004/007/008; AC-F-001.1, SCN-01."""
    ref = new_ref(api, tags=[' #Dark ', 'style:clean', 'dark'], notes='Original')
    assert ref['category'] == 'General'
    assert sorted(ref['tags']) == ['dark', 'style:clean']
    path = '/references/' + ref['id']
    assert api('GET', path, template='/references/{id}') == ref
    changed = api('PUT', path, {'title': 'Updated', 'tags': [], 'image_url': None}, template='/references/{id}')
    assert changed['title'] == 'Updated' and changed['tags'] == []
    assert changed['notes'] == 'Original' and changed['url'] == ref['url']
    api('DELETE', path, status=204, template='/references/{id}')
    api('GET', path, status=404, template='/references/{id}')
    api('DELETE', path, status=404, template='/references/{id}')


@pytest.mark.parametrize('body,status', [({},400), ({'title':'','url':'https://a.org'},400),
    ({'title':' '*3,'url':'https://a.org'},400), ({'title':'x'*256,'url':'https://a.org'},400),
    ({'title':4,'url':'https://a.org'},400), ({'title':'x','url':''},400),
    ({'title':'x','url':'javascript:alert(1)'},422), ({'title':'x','url':'data:text/html,x'},422),
    ({'title':'x','url':'ftp://a.org'},422), ({'title':'x','url':'https://'},400),
    ({'title':'x','url':'https://a.org','tags':'x'},400),
    ({'title':'x','url':'https://a.org','tags':[1]},400),
    ({'title':'x','url':'https://a.org','image_url':'javascript:x'},422),
    ({'title':'x','url':'https://a.org','notes':None},400), ([],400)])
def test_input_rejection(api, body, status):
    """SCN-02 / REQ-NF-004: invalid requests leave state unchanged."""
    api('POST', '/references', body, status)
    assert api('GET', '/references')['total'] == 0


def test_malformed_json_and_atomic_update(api):
    api('POST', '/references', raw=b'{', status=400)
    ref = new_ref(api)
    path = '/references/' + ref['id']
    api('PUT', path, {'title':'Changed', 'image_url':'data:x'}, 422, '/references/{id}')
    assert api('GET', path, template='/references/{id}') == ref
    api('PUT', '/references/missing', {}, 404, '/references/{id}')


def test_search_filter_and_pagination(api):
    """SCN-03/04/06, REQ-F-005/006: AND, combined filters, case and boundaries."""
    a = new_ref(api, tags=['mobile','dark','style:clean'], notes='Українська нотатка', category='UI/UX')
    new_ref(api, title='Other', tags=['mobile'], category='Branding')
    new_ref(api, title='Third', tags=['dark'])
    for query in ['tags=mobile,dark', 'tags=style:clean', 'q=DASHBOARD&category=UI%2FUX', 'q=%D0%BD%D0%BE%D1%82%D0%B0%D1%82%D0%BA%D0%B0']:
        assert [r['id'] for r in api('GET','/references?'+query)['items']] == [a['id']]
    assert api('GET','/references?q=') ['total'] == 3
    assert api('GET','/references?limit=1&offset=1')['total'] == 3
    assert len(api('GET','/references?limit=1&offset=1')['items']) == 1
    assert api('GET','/references?offset=999')['items'] == []
    assert api('GET','/references?q=absent')['items'] == []


@pytest.mark.parametrize('query', ['limit=0','limit=101','limit=x','offset=-1','offset=1.5'])
def test_bad_pagination(api, query):
    api('GET', '/references?'+query, status=400)


def test_categories(api):
    """SCN-05: default protected, migration preserves all references."""
    assert {'name':'General','is_default':True} in api('GET','/categories')
    api('POST','/categories',{'name':'Custom'},201)
    api('POST','/categories',{'name':'Custom'},400)
    api('POST','/categories',{'name':''},400)
    ref = new_ref(api, category='Custom', notes='Preserve')
    result = api('DELETE','/categories/Custom',template='/categories/{name}')
    assert result['affected_references_count'] == 1 and result['reassigned_to'] == 'General'
    saved = api('GET','/references/'+ref['id'],template='/references/{id}')
    assert saved == {**ref,'category':'General'}
    api('DELETE','/categories/General',status=400,template='/categories/{name}')
    api('DELETE','/categories/missing',status=404,template='/categories/{name}')
    api('DELETE','/categories/UI%2FUX',template='/categories/{name}')


def test_collections(api):
    """SCN-07: N:M, idempotent link, unlink and cascade cleanup."""
    ref = new_ref(api)
    col = api('POST','/collections',{'name':'Board','description':'Moodboard'},201)
    other = api('POST','/collections',{'name':'Other'},201)
    assert len(api('GET','/collections')) == 2
    api('POST','/collections',{'name':' '*2},400)
    path = '/collections/'+col['id']
    link = path+'/references/'+ref['id']
    template = '/collections/{id}/references/{ref_id}'
    for _ in range(2):
        assert api('POST',link,template=template)['reference_ids'] == [ref['id']]
    api('POST','/collections/'+other['id']+'/references/'+ref['id'],template=template)
    assert api('GET','/collections')[0]['reference_count'] == 1
    api('DELETE',link,status=204,template=template)
    assert api('GET',path,template='/collections/{id}')['reference_ids'] == []
    api('GET','/references/'+ref['id'],template='/references/{id}')
    api('DELETE',path,status=204,template='/collections/{id}')
    api('GET',path,status=404,template='/collections/{id}')
    api('DELETE','/references/'+ref['id'],status=204,template='/references/{id}')
    assert api('GET','/collections/'+other['id'],template='/collections/{id}')['reference_ids'] == []
    api('POST','/collections/'+other['id']+'/references/missing',status=404,template=template)
    api('DELETE','/collections/missing',status=404,template='/collections/{id}')


def test_health_persistence_and_audit(api):
    """SRS 3.1 local storage, lab5 action logging, REQ-NF-005."""
    assert api('GET','/health')['status'] == 'healthy'
    ref = new_ref(api)
    from src.api import create_app
    restored = create_app(api.tmp/'catalog.json', api.tmp/'audit.jsonl')
    assert restored.service.catalog.references[ref['id']].title == ref['title']
    api('POST','/references',{},400)
    rows = [json.loads(line) for line in (api.tmp/'audit.jsonl').read_text().splitlines()]
    requests = [r for r in rows if r['event'] == 'request']
    assert [r['status'] for r in requests] == [200,201,400]
    assert all(r['request_id'] and r['duration_ms'] >= 0 for r in requests)
    assert 'Dashboard' not in (api.tmp/'audit.jsonl').read_text()
