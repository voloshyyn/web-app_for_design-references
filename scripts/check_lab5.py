"""One command for regression, coverage, contract checks, and evidence export."""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from lab5_status import report_status

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
env = dict(os.environ, PYTHONPATH=str(ROOT/'.lab5-deps'), PYTHONUTF8='1')


def run(arguments, output):
    result = subprocess.run([sys.executable, '-X', 'utf8', *arguments], env=env,
                            capture_output=True, text=True, encoding='utf-8')
    text = result.stdout + result.stderr
    (ROOT/output).write_text(text, encoding='utf-8')
    print(text, end='')
    return result.returncode


code = run(['-m','coverage','run','--source=src','-m','pytest','tests','-q',
            '-p','no:cacheprovider','--junitxml=logs/lab5-junit.xml'], 'logs/lab5-final-tests.txt')
coverage_code = run(['-m','coverage','json','-o','logs/lab5-coverage.json'], 'logs/lab5-coverage-export.txt')
run(['-m','coverage','report','-m'], 'logs/lab5-coverage.txt')
percentage = 0
if coverage_code == 0:
    coverage = json.loads((ROOT/'logs/lab5-coverage.json').read_text())
    model = next(v for k,v in coverage['files'].items() if k.replace('\\','/').endswith('src/models.py'))
    percentage = model['summary']['percent_covered']
    if percentage < 95:
        code = 1
status = 'PASS' if code == 0 and coverage_code == 0 else 'FAIL'
validation_code = run(['scripts/validate_lab5.py'], 'logs/lab5-agent-validation.txt')
validation = json.loads((ROOT/'logs/lab5-agent-validation.json').read_text(encoding='utf-8')) if validation_code == 0 else {'status':'FAIL'}
decision = report_status({'automated_status': status}, validation)
(ROOT/'logs/lab5-verification.json').write_text(json.dumps(dict(
    timestamp=datetime.now(timezone.utc).isoformat(), automated_status=status,
    model_coverage_percent=percentage, **{k:v for k,v in decision.items() if k != 'automated_status'}), indent=2), encoding='utf-8')
print(f'Automated verification: {status}; model coverage: {percentage:.1f}%; delegated technical gate: {decision["technical_gate"]}')
sys.exit(0 if decision['technical_gate'] == 'GO' else 1)
