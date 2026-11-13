"""Contract-driven WSGI routing; runtime uses Python standard library only."""
import argparse
import json
import re
import time
from http import HTTPStatus
from pathlib import Path
from threading import RLock
from urllib.parse import parse_qs
from uuid import uuid4
from wsgiref.simple_server import make_server

from src.audit import Audit, timestamp
from src.repository import Repository
from src.service import Service, ApiError

ROOT = Path(__file__).resolve().parents[1]


def problem(status, code, detail, path):
    """One representation for expected and unexpected failures."""
    return dict(type='about:blank', title=HTTPStatus(status).phrase, status=status,
                detail=detail, code=code, timestamp=timestamp(), instance=path)


class Application:
    def __init__(self, data_path, log_path):
        self.service = Service(Repository(data_path))
        self.audit = Audit(log_path)
        self.lock = RLock()
        self.contract = json.loads((ROOT/'spec/openapi.json').read_text(encoding='utf-8'))
        self.routes = []
        for path, methods in self.contract['paths'].items():
            pattern = re.sub(r'\{(\w+)\}', lambda m: '(?P<' + m[1] + '>' +
                             ('.+' if m[1] == 'name' else '[^/]+') + ')', path)
            for method, operation in methods.items():
                if method in {'get','post','put','delete'}:
                    self.routes.append((method.upper(), re.compile('^/api/v1'+pattern+'$'), operation))
        self.audit.write('startup', version=self.contract['info']['version'])

    def __call__(self, environ, start_response):
        started = time.perf_counter()
        request_id = uuid4().hex
        method = environ['REQUEST_METHOD']
        path = environ.get('PATH_INFO','').encode('latin-1').decode('utf-8')
        operation_id = 'unmatched'
        with self.lock:
            try:
                route = next(((p.match(path), o) for m, p, o in self.routes
                              if m == method and p.match(path)), None)
                if route is None:
                    raise ApiError(404, 'RESOURCE_NOT_FOUND', 'Route does not exist.')
                match, operation = route
                operation_id = operation['operationId']
                body = {}
                if 'requestBody' in operation:
                    try:
                        length = int(environ.get('CONTENT_LENGTH') or 0)
                        if length < 1 or length > 1048576:
                            raise ValueError('Invalid body size')
                        body = json.loads(environ['wsgi.input'].read(length))
                        if not isinstance(body, dict):
                            raise ValueError('Object expected')
                    except (ValueError, UnicodeError):
                        raise ApiError(400, 'MALFORMED_REQUEST', 'Expected a JSON object (max 1 MiB).')
                query = {k: v[-1] for k, v in parse_qs(environ.get('QUERY_STRING',''), keep_blank_values=True).items()}
                status, payload = self.service.execute(operation_id, match.groupdict(), query, body)
            except ApiError as error:
                status = error.status
                payload = problem(status, error.code, error.detail, path)
            except Exception as error:
                status = 500
                self.audit.write('error', request_id=request_id, error_type=type(error).__name__)
                payload = problem(500, 'INTERNAL_ERROR', 'An unexpected error occurred.', path)
            # Escape HTML-sensitive characters in JSON without changing decoded values.
            encoded = b'' if status == 204 else json.dumps(payload, ensure_ascii=True).replace(
                '<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026').encode('utf-8')
            self.audit.write('request', request_id=request_id, method=method, operation=operation_id,
                             status=status, duration_ms=round((time.perf_counter()-started)*1000, 3))
        media = 'application/problem+json' if status >= 400 else 'application/json'
        start_response(f'{status} {HTTPStatus(status).phrase}', [
            ('Content-Type', media+'; charset=utf-8'), ('Content-Length', str(len(encoded))),
            ('X-Request-ID', request_id), ('X-Content-Type-Options','nosniff')])
        return [encoded]


def create_app(data_path=ROOT/'data/catalog.json', log_path=ROOT/'logs/runtime/api.jsonl'):
    return Application(data_path, log_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    app = create_app()
    with make_server('127.0.0.1', args.port, app) as server:
        print(f'API: http://127.0.0.1:{args.port}/api/v1/health', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            app.audit.write('shutdown')


if __name__ == '__main__':
    main()
