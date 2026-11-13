"""Audit follow-up: tests written before fixes, 2026-11-15."""
import io
import json

from test_api import api


def test_malformed_path_is_logged_as_problem(api):
    responses = []
    raw = b''.join(api.app({
        'REQUEST_METHOD': 'GET', 'PATH_INFO': '/api/v1/categories/\xff',
        'QUERY_STRING': '', 'wsgi.input': io.BytesIO(),
    }, lambda status, headers: responses.append((status, dict(headers)))))
    assert responses[0][0].startswith('400 ')
    assert responses[0][1]['Content-Type'].startswith('application/problem+json')
    problem = json.loads(raw)
    assert problem['code'] == 'MALFORMED_REQUEST'
    rows = [json.loads(line) for line in (api.tmp/'audit.jsonl').read_text().splitlines()]
    event = rows[-1]
    assert event['event'] == 'request' and event['status'] == 400
    assert event['request_id'] == responses[0][1]['X-Request-ID']


def test_health_reports_current_contract_version(api):
    assert api('GET', '/health')['version'] == api.app.contract['info']['version']


def test_report_status_never_promotes_failed_or_missing_evidence():
    from scripts.lab5_status import report_status
    assert report_status({'automated_status': 'FAIL'}, {'status': 'PASS'})['technical_gate'] == 'REVISE'
    assert report_status({}, {})['technical_gate'] == 'REVISE'
    result = report_status({'automated_status': 'PASS'}, {'status': 'FAIL'})
    assert result['technical_gate'] == 'REVISE'
    result = report_status({'automated_status': 'PASS'}, {'status': 'PASS'})
    assert result['technical_gate'] == 'GO'
    assert result['validation_actor'] == 'Codex (delegated by user)'
    assert result['human_validation'] == 'NOT_PERFORMED'
