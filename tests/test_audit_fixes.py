"""Audit follow-up: tests written before fixes, 2026-11-15."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

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


def test_generated_report_keeps_failed_status(tmp_path):
    """Exercise the actual generator with failed evidence, not only its helper."""
    root = Path(__file__).resolve().parents[1]
    for directory in ['scripts', 'logs', 'docs']:
        (tmp_path/directory).mkdir()
    for name in ['report_lab5.py','lab5_status.py']:
        shutil.copyfile(root/'scripts'/name, tmp_path/'scripts'/name)
    for name, content in {
        'lab5-verification.json': {'automated_status':'FAIL'},
        'lab5-agent-validation.json': {'status':'FAIL','observations':['FAILED acceptance scenario']},
    }.items():
        (tmp_path/'logs'/name).write_text(json.dumps(content),encoding='utf-8')
    (tmp_path/'logs/lab5-final-tests.txt').write_text('1 failed',encoding='utf-8')
    (tmp_path/'docs/lab5-form-answers.md').write_text('Test fixture',encoding='utf-8')
    process = subprocess.run([sys.executable,'-X','utf8',str(tmp_path/'scripts/report_lab5.py')],
                             capture_output=True,text=True,encoding='utf-8')
    assert process.returncode == 0, process.stderr
    report = (tmp_path/'docs/lab5-report.md').read_text(encoding='utf-8')
    assert 'Автоматизована верифікація: FAIL' in report
    assert 'Поточний технічний Gate: REVISE' in report
    assert 'серверна перевірка PASS' not in report
    assert (tmp_path/'output/pdf/lab5-report.pdf').read_bytes().startswith(b'%PDF')
