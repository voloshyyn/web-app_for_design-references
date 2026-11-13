"""Generate a protocol from current evidence; no fixed success claims."""
import json
import os
from pathlib import Path
import subprocess
from xml.sax.saxutils import escape
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from lab5_status import report_status

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)


def evidence(name):
    path = ROOT/'logs'/name
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


verification = evidence('lab5-verification.json')
validation = evidence('lab5-agent-validation.json')
status = report_status(verification, validation)
coverage = evidence('lab5-coverage.json')
performance = evidence('lab5-performance.json')
faults = evidence('lab5-fault-detection.json')
summary = (ROOT/'logs/lab5-final-tests.txt').read_text(encoding='utf-8')
history = subprocess.run(['git','log','--format=%h %s','-12'],capture_output=True,text=True,encoding='utf-8').stdout
# Fixed project identity, current evidence and generation date.
try:
    today = datetime.now(ZoneInfo('Europe/Kyiv')).date().isoformat()
except Exception:
    today = '2026-11-15'
sections = [
('Лабораторна робота №5', f'''Проектування інформаційних систем
SDD + TDD: REST API та керована зміна специфікації
Студент: Андрій Волошин, КН-31. Агент: Codex.
Дата актуалізації: {today}.

Мета: реалізувати REST API за затвердженим OpenAPI; перевірити вимоги
тестами; виконати рефакторинг, журналювання та одну зміну через адендум.
Джерела: усі 11 сторінок PDF завдання, SRS 1.0, SCN-01..07, API-GATE,
OpenAPI 1.0.0, план, реєстр ризиків, матриця простежуваності.

Автоматизована верифікація: {status['automated_status']}.
Валідація агентом: {status['agent_validation']}.
Поточний технічний Gate: {status['technical_gate']}.
Виконавець валідації: Codex, за прямим дорученням користувача 15.11.2026.
Людська валідація: {status['human_validation']}.

Технічне рішення стосується серверної частини. Воно не є твердженням,
що виконана буквально вимога PDF про валідацію людиною. Історичний
поетапний RED бази не відновлюється заднім числом. Ці межі явно збережено.'''),
('1. План, архітектура та базовий TDD', '''План: вимоги -> тести -> TEST-GATE -> API -> рефакторинг -> адендум ->
нові тести -> код -> регресія -> валідація -> протокол.
База: 15 API-операцій; після ADD-001: 16. Сервер на стандартному Python,
локальне JSON-сховище, без зовнішньої БД, Docker або хмарного сервісу.
api.py: транспорт/маршрути; service.py: бізнес-операції; models.py: домен;
repository.py: атомарне збереження; audit.py: структуровані журнали.

До сервера створено 26 HTTP-сценаріїв із SRS/OpenAPI: CRUD, категорії,
N:M-колекції, нормалізація тегів, AND-фільтрація, пошук, пагінація,
позитивні/негативні/граничні запити. Схеми відповідей читаються з контракту.
Початковий RED: 26 setup errors через відсутність src.api. Це слабший
доказ, ніж окреме поведінкове непроходження кожної вимоги; не приховується.
Перший код виявив дефект маршрутизації DELETE зв'язку, виправлений без
послаблення тестів. GREEN бази: 35 passed із 9 старими доменними тестами.
Рефакторинг формування ProblemDetails: повторно 35 passed.

На 15.11.2026 додано контроль чутливості: окремі операції вимикаються
лише в тестовому процесі, відповідні HTTP-тести мають впасти з 501.
Це поточна fault-injection перевірка, не історичний RED і не доказ
всіх можливих мутацій бізнес-логіки. Доказ: logs/lab5-fault-detection.json.
Історія git збережена без переписування.'''),
('2. Адендум, тікет та виправлення аудиту', '''ADD-001 / REQ-F-009: перейменування колекції без втрати ID, опису та
зв'язків. PUT /collections/{id}; name: непорожній string 1..100 символів;
400/404 при помилці, ідемпотентність, перезапуск та аудит.
Вимога: spec/addendum-001-collection-rename.md.
Повний локальний тікет: docs/tickets/LAB5-04.md.

Спочатку вимога/OpenAPI 1.1.0, потім 8 тестів RED (404 замість 200/400),
потім код: 43 passed. Рефакторинг: спільна перевірка назви колекції.
Базовий контракт збережено в spec/openapi-baseline.json; автоматично
перевіряються незмінність його операцій/DTO та еквівалентність YAML/JSON.

Аудит 15.11.2026: перед виправленнями записано три відмови нових тестів.
Виправлено некоректний UTF-8 у path: тепер 400 ProblemDetails та запис
аудиту з request_id. Health отримує версію з актуального контракту.
Статус протоколу обчислюється з доказів; FAIL або відсутні докази не можуть
дати технічний GO. Підтверджено регресійними тестами.

Поточне прийняття делеговано користувачем агенту. Історичні записи Gate
не підмінено підписом людини. PDF вимагає тікет, але не GitHub як платформу;
локальний файл є самодостатнім тікетом, публікація не виконується.'''),
('3. Фактичні результати верифікації', f'''Статус: {status['automated_status']}.
Підсумок останнього pytest:
{summary.strip()}

Покриття рядків моделей: {verification.get('model_coverage_percent',0):.2f}%.
Загальне покриття src: {coverage.get('totals',{}).get('percent_covered',0):.2f}%.
Поріг моделей за SRS: 95%. Line coverage не означає повноти вимог.

1000 референсів; 20 повторень кожної операції:
AND за 3 тегами, максимум: {performance.get('filter',{}).get('max_ms',0):.3f} мс.
Пошук, максимум: {performance.get('search',{}).get('max_ms',0):.3f} мс.
Це доменний час, не мережевий або браузерний end-to-end показник.
Контроль вимкнення операцій: {faults.get('status','MISSING')}.
Виявлено: {sum(bool(c['detected']) for c in faults.get('cases',[]))} / {len(faults.get('cases',[]))} перевірок.

Перевіряються цілісність категорій/колекцій, rollback при OSError,
відсутність перезапису пошкодженого JSON, збереження після перезапуску,
DTO/коди/Content-Type, сумісність специфікацій та журнали успіхів/відмов.
Аудит не записує тіла запитів і нотатки; містить час, operationId, статус,
request_id, тривалість. Некоректний path також проходить аудит.
Докази: logs/lab5-final-tests.txt, lab5-coverage.json, lab5-performance.json,
lab5-audit-red.txt, lab5-fault-detection.json та lab5-agent-validation.json.'''),
('4. Делегована валідація та межі', f'''Статус сценарію: {status['agent_validation']}.
Сценарій відповідає потребі дизайнера: зберегти натхнення, знайти потрібне,
зібрати дошку, перейменувати її під проєкт і зберегти роботу після рестарту.
Сценарій виконується через справжній HTTP на тимчасових даних.

''' + '\n\n'.join(validation.get('observations',['Докази відсутні.'])) + '''

Агент оцінює відповідність цьому сценарію, але не замінює емпіричну
оцінку реальної людини. User mandate: «валідуй замість людини» (15.11.2026).
Буквальна вимога PDF «валідація людиною» лишається невиконаною.
UX «до 3 кліків» і візуальна картка SRS не заявляються виконаними: тут API.

Запуск: .\\lab5.ps1 test; .\\lab5.ps1 validate; .\\lab5.ps1 audit;
.\\lab5.ps1 demo; .\\lab5.ps1 serve; .\\lab5.ps1 report.
Команда test повторює верифікацію та валідаційний сценарій; audit додатково
перевіряє виявлення вимкнених операцій. Сервер: 127.0.0.1:8000, Ctrl+C.
Дані: data/catalog.json; журнал: logs/runtime/api.jsonl.
Резервне копіювання/відновлення JSON виконуються при зупиненому сервері.
Форму Google не надіслано, відеозахист не записано.'''),
('5. Контрольні відповіді', (ROOT/'docs/lab5-form-answers.md').read_text(encoding='utf-8')),
('6. Історія та рішення', f'''Поточний технічний Gate: {status['technical_gate']}.
Виконавець: {status['validation_actor']}.
Формальна відповідність буквальній людській валідації: не заявляється.
Історичне обмеження TDD бази: збережено, не виправляється заднім числом.
Тікет: docs/tickets/LAB5-04.md; RTM: spec/traceability-matrix.md.
Детальний висновок: logs/lab5-final-gate.md.

Знімок останніх комітів:
{history}''')
]
(ROOT/'docs/lab5-report.md').write_text('\n\n'.join('# '+title+'\n\n'+body for title,body in sections),encoding='utf-8')
font_candidates = [Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/arial.ttf',Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
font = next((p for p in font_candidates if p.exists()),None)
if font is None:
    raise RuntimeError('Arial or DejaVu Sans is required.')
pdfmetrics.registerFont(TTFont('LabFont',str(font)))
heading = ParagraphStyle('Heading',fontName='LabFont',fontSize=17,leading=23,spaceAfter=18,textColor=colors.HexColor('#17334d'))
body_style = ParagraphStyle('Body',fontName='LabFont',fontSize=10.5,leading=15,spaceAfter=10)
story=[]
for i,(title,body) in enumerate(sections):
    if i:
        story.append(PageBreak())
    story.append(Paragraph(escape(title),heading))
    for block in body.split('\n\n'):
        if block.strip():
            story.append(Paragraph(escape(block.strip()).replace('\n','<br/>'),body_style))
output = ROOT/'output/pdf/lab5-report.pdf'
output.parent.mkdir(parents=True,exist_ok=True)


def footer(canvas,doc):
    canvas.setFont('LabFont',8)
    canvas.drawString(42,25,'ЛР5 | SDD + TDD | Андрій Волошин | КН-31')
    canvas.drawRightString(A4[0]-42,25,str(doc.page))


SimpleDocTemplate(str(output),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=45,title='Лабораторна робота 5',author='Андрій Волошин / Codex').build(story,onFirstPage=footer,onLaterPages=footer)
print(output)
