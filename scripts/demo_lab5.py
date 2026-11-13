"""Disposable live HTTP demo; does not change the user's catalog."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.request import Request, urlopen
from wsgiref.simple_server import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.api import create_app

with TemporaryDirectory() as directory:
    root = Path(directory)
    server = make_server('127.0.0.1', 0, create_app(root/'data.json',root/'audit.jsonl'))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def call(method,path,body=None):
        data = json.dumps(body).encode() if body is not None else None
        with urlopen(Request(f'http://127.0.0.1:{server.server_port}/api/v1'+path,
                             data=data, method=method, headers={'Content-Type':'application/json'})) as response:
            raw = response.read()
            result = json.loads(raw) if raw else None
            print(method,path,response.status,json.dumps(result,ensure_ascii=False))
            return result

    try:
        call('GET','/health')
        ref = call('POST','/references',{'title':'Lab 5 dashboard','url':'https://example.org',
                                       'tags':['mobile','dark','style:clean']})
        call('GET','/references?tags=mobile,dark')
        col = call('POST','/collections',{'name':'Moodboard'})
        path = '/collections/'+col['id']
        call('POST',path+'/references/'+ref['id'])
        call('PUT',path,{'name':'Client pitch'})
        call('GET',path)
        print('Demo complete. Temporary data only; no human validation implied.')
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
