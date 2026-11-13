"""Present-day behavioral RED probes, never presented as historical TDD evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('REQ-F-001','createReference','test_api.py::test_reference_lifecycle'),
    ('REQ-F-002','deleteCategory','test_api.py::test_categories'),
    ('REQ-F-003','addReferenceToCollection','test_api.py::test_collections'),
    ('REQ-F-004','updateReference','test_api.py::test_reference_lifecycle'),
    ('REQ-F-005','listReferences','test_api.py::test_search_filter_and_pagination'),
    ('REQ-F-006','listReferences','test_api.py::test_search_filter_and_pagination'),
    ('REQ-F-007','getReferenceById','test_api.py::test_reference_lifecycle'),
    ('REQ-F-008','deleteReference','test_api.py::test_reference_lifecycle'),
    ('REQ-F-009','updateCollection','test_addendum.py::test_rename_preserves_identity_links_and_persistence'),
]
PLUGIN = '''import os
import pytest
from src.service import Service, ApiError
@pytest.fixture(autouse=True)
def disable_one_operation(monkeypatch):
    original = Service.dispatch
    def dispatch(self, operation, params, query, body):
        if operation == os.environ['LAB5_DISABLED_OPERATION']:
            raise ApiError(501, 'INJECTED_MISSING_BEHAVIOR', 'Audit fault injection')
        return original(self, operation, params, query, body)
    monkeypatch.setattr(Service, 'dispatch', dispatch)
'''


def main():
    records = []
    with TemporaryDirectory() as directory:
        Path(directory,'lab5_probe.py').write_text(PLUGIN,encoding='utf-8')
        for requirement,operation,test in CASES:
            env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT/'.lab5-deps'),directory,str(ROOT)]),
                       PYTHONUTF8='1',LAB5_DISABLED_OPERATION=operation)
            run = subprocess.run([sys.executable,'-X','utf8','-m','pytest','tests/'+test,
                                  '-q','-p','no:cacheprovider','-p','lab5_probe'],
                                 cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
            output = run.stdout+run.stderr
            detected = run.returncode == 1 and 'AssertionError' in output and '501' in output and '1 failed' in output
            records.append(dict(requirement=requirement,operation=operation,test=test,
                                detected=detected,exit_code=run.returncode))
            (ROOT/f'logs/lab5-probe-{requirement}.txt').write_text(output,encoding='utf-8')
            print(requirement, operation, 'DETECTED' if detected else 'NOT DETECTED',flush=True)
    result = dict(timestamp=datetime.now(timezone.utc).isoformat(),
                  kind='Current operation-disable fault injection, not historical TDD',
                  status='PASS' if all(r['detected'] for r in records) else 'FAIL',cases=records)
    (ROOT/'logs/lab5-fault-detection.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return 0 if result['status']=='PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
