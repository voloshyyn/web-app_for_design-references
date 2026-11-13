"""Delegated user-journey acceptance through HTTP, with a real server restart."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from wsgiref.simple_server import make_server, WSGIRequestHandler
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.api import create_app


class Quiet(WSGIRequestHandler):
    def log_message(self, *args):
        pass


def main():
    observations = []
    result = {'timestamp': datetime.now(timezone.utc).isoformat(), 'actor': 'Codex',
              'authorization': 'User delegated validation on 2026-11-15',
              'status': 'FAIL', 'human_validation': 'NOT_PERFORMED',
              'scope': 'REST API user journey; UI click-count not evaluated',
              'observations': observations}
    with TemporaryDirectory() as directory:
        root = Path(directory)
        server = thread = None

        def start():
            nonlocal server, thread
            server = make_server('127.0.0.1', 0, create_app(root/'catalog.json',root/'audit.jsonl'),
                                 handler_class=Quiet)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()

        def stop():
            if server is not None:
                server.shutdown()
                server.server_close()
                thread.join()

        def call(method, path, body=None, expected=200):
            data = json.dumps(body).encode() if body is not None else None
            req = Request(f'http://127.0.0.1:{server.server_port}/api/v1'+path, data=data,
                          method=method, headers={'Content-Type': 'application/json'})
            try:
                response = urlopen(req)
            except HTTPError as error:
                response = error
            with response:
                raw = response.read()
                assert response.status == expected, (method, path, response.status, raw)
                return json.loads(raw) if raw else None

        try:
            start()
            call('POST','/categories',{'name':'Pitch'},201)
            first = call('POST','/references',{'title':'Banking mobile dashboard',
                         'url':'https://example.org/dashboard', 'category':'Pitch',
                         'tags':[' Mobile ', '#Dark', 'style:clean'], 'notes':'For client pitch'},201)
            call('POST','/references',{'title':'Unrelated branding','url':'https://example.org/logo',
                                      'tags':['branding']},201)
            found = call('GET','/references?tags=mobile,dark&q=CLIENT&category=Pitch')
            assert [item['id'] for item in found['items']] == [first['id']]
            observations.append('PASS: designer saves inspiration and retrieves only relevant material using combined filters.')
            board = call('POST','/collections',{'name':'Draft pitch','description':'Client board'},201)
            path = '/collections/'+board['id']
            call('POST',path+'/references/'+first['id'])
            renamed = call('PUT',path,{'name':'Approved pitch'})
            assert renamed == {'id':board['id'],'name':'Approved pitch',
                               'description':'Client board','reference_ids':[first['id']]}
            observations.append('PASS: ADD-001 avoids rebuilding a board; identity, description and saved inspiration remain intact.')
            call('PUT',path,{'name':'   '},400)
            assert call('GET',path) == renamed
            stop()
            start()
            assert call('GET',path) == renamed
            observations.append('PASS: invalid rename changes nothing; accepted rename survives a complete HTTP server restart.')
            migration = call('DELETE','/categories/Pitch')
            assert migration['affected_references_count'] == 1
            card = call('GET','/references/'+first['id'])
            assert card == {**first,'category':'General'}
            call('DELETE',path,expected=204)
            assert call('GET','/references/'+first['id']) == card
            observations.append('PASS: reorganizing categories and deleting a board preserves the source reference and notes.')
            rows = [json.loads(line) for line in (root/'audit.jsonl').read_text().splitlines()]
            requests = [row for row in rows if row['event']=='request']
            assert len(requests) == 14 and sum(row['status']==400 for row in requests) == 1
            observations.append('PASS: all 14 HTTP actions, including rejection, have audit records.')
            result['status'] = 'PASS'
        except Exception as error:
            result['error'] = f'{type(error).__name__}: {error}'
        finally:
            stop()
    (ROOT/'logs/lab5-agent-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
