"""Rebuild the Ukrainian lab protocol from actual test evidence, with Cyrillic PDF fonts."""
import json
import os
from pathlib import Path
import re
import subprocess
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
verification = json.loads(Path('logs/lab5-verification.json').read_text(encoding='utf-8'))
coverage = json.loads(Path('logs/lab5-coverage.json').read_text(encoding='utf-8'))
performance = json.loads(Path('logs/lab5-performance.json').read_text(encoding='utf-8'))
test_output = Path('logs/lab5-final-tests.txt').read_text(encoding='utf-8')
test_summary = next((line for line in test_output.splitlines() if re.search(r'\d+ passed',line)), 'See test log')
history = subprocess.run(['git','log','--format=%h %s','-8'],capture_output=True,text=True,encoding='utf-8').stdout

sections = [
('Лабораторна робота №5', '''Проектування інформаційних систем
SDD + TDD: реалізація REST API та керована зміна специфікації

Студент: Андрій Волошин
Група: КН-31 (за чинною SRS)
Кодинговий агент: Codex
Дата виконання: 14 листопада 2026 року
Проєкт: Система каталогізації та швидкого пошуку дизайн-референсів
Репозиторій: github.com/voloshyyn/web-app_for_design-references

Мета: реалізувати API за затвердженим контрактом; створити тести до нового
серверного коду; виконати рефакторинг і одну змістовну зміну через адендум;
розрізняти автоматизовану верифікацію та людську валідацію.

Опрацьовано всі 11 сторінок завдання. Протокол містить фактичні результати,
посилання на артефакти, контрольні відповіді й незавершені людські перевірки.
Статус: автоматизована серверна перевірка PASS; підсумковий Gate REVISE
до валідації студентом. Це не підпис або свідчення перевірки людиною.'''),
('1. Вхідні дані та план', Path('docs/lab5-plan.md').read_text(encoding='utf-8') + '''

У репозиторії наявні SRS, BDD, глосарій, беклог, реєстр ризиків та API-GATE
зі статусом GO. Початковий контракт містив 15 операцій. Наявні моделі та
9 старих тестів передували ЛР5; їх авторство й хронологію не приписано
новому TDD-циклу. Файл logs/mock-validation-report.md мав користувацькі
зміни до початку роботи та не включався до нових комітів.

Локальні тікети LAB5-01..06 визначені планом та підсумковим Gate.
Публікація GitHub Issues і надсилання Google Форми не виконувалися.'''),
('2. TDD та реалізація бази', '''Тести tests/test_api.py створено з вимог і OpenAPI до src/api.py.
26 сценаріїв охоплюють створення/читання/оновлення/видалення референсів,
категорії, N:M-колекції, теги, пошук, пагінацію та health.
Для кожної відповіді перевіряються HTTP-код, Content-Type та схема
контракту; для 204 - відсутність тіла. Негативні сценарії включають
небезпечні протоколи, помилки JSON, типів і довжини, відсутні ресурси.

RED бази: 26 setup errors через відсутність серверного модуля. Це доказ
відсутності реалізації, а не 26 окремих поведінкових відмов.
Технічний TEST-GATE записаний до коду. Перший запуск реалізації виявив
помилку маршруту видалення зв'язку з колекцією; шаблон маршруту виправлено
без зміни очікувань тесту. GREEN: 35 passed, включно з 9 старими тестами.

Компоненти: api.py - HTTP/маршрути; service.py - операції та транзакції;
models.py - домен; repository.py - атомарне JSON-збереження;
audit.py - структурований JSONL-аудит. Сервер не має сторонніх залежностей.
Помилка запису відновлює стан у пам'яті; старий файл залишається цілим.

Базовий рефакторинг: спільна функція ProblemDetails замість дублювання
формування помилок. Повторно 35 passed. Старий контракт не змінювався.
Докази: logs/lab5-baseline-red.txt, baseline-green.txt, baseline-refactor.txt
(усі назви мають префікс lab5-), logs/lab5-test-gate.md.'''),
('3. Адендум і повторний цикл', '''ADD-001 / LAB5-04 / REQ-F-009: перейменування колекції.
Потреба: після зміни назви проєкту зберегти дошку й усі її прив'язки.
Окремий документ: spec/addendum-001-collection-rename.md.
Критерії: PUT /collections/{id}, обов'язкова непорожня назва 1..100 символів;
ID, опис і reference_ids незмінні; 400 при некоректній назві, 404 для
відсутньої дошки; ідемпотентність, збереження після перезапуску та аудит.

Спочатку збережено базовий OpenAPI у spec/openapi-baseline.json.
Контракт 1.1.0 додає лише updateCollection та CollectionUpdateDto.
Технічна рекомендація SPEC-ADDENDUM-GATE зафіксована окремо;
людський підпис не імітується. Потім створено 8 тестів tests/test_addendum.py.

RED: усі 8 тестів не проходили з очікуваної причини: 404 замість 200/400.
Це реальні поведінкові відмови запущеного сервера до реалізації зміни.
Після TEST-GATE реалізовано перейменування. GREEN: 43 passed.
Рефакторинг: спільна функція перевірки назви для створення і перейменування.
Змінені очікування тестів не використовувалися для досягнення GREEN.

Докази: logs/lab5-addendum-gate.md, lab5-addendum-test-gate.md,
lab5-addendum-red.txt, lab5-addendum-green.txt. Тести сумісності порівнюють
всі базові операції та DTO з актуальним контрактом.'''),
('4. Верифікація та аналіз журналів', f'''Фактичний фінальний запуск: {test_summary}
Статус: {verification['automated_status']}.
Покриття рядків моделей: {verification['model_coverage_percent']:.2f}% (поріг SRS 95%).
Загальне покриття рядків src: {coverage['totals']['percent_covered']:.2f}%.
Це не branch coverage та не доказ повноти вимог.

Навантаження: 1000 референсів, 20 повторень кожної операції.
Максимум AND-фільтрації за 3 тегами: {performance['filter']['max_ms']:.3f} мс.
Максимум пошуку: {performance['search']['max_ms']:.3f} мс.
Вимога <50 мс виконана для доменного коду на цій машині, не для всього UI.

Перевірено валідність OpenAPI 1.0.0 і 1.1.0, еквівалентність YAML/JSON,
незмінність старих операцій, схеми відповідей усіх 16 HTTP-операцій.
Тести faults: збій os.replace дає 500, старий файл і попередній стан
збережені; пошкоджений JSON не перезаписується; відновлено зв'язки та опис
колекцій після перезапуску. Виняток не розкриває приватні деталі клієнту.

Аудит: timestamp, event, operation, method, status, request_id, duration_ms.
У журналі є успішні та відхилені дії; тіла, нотатки й параметри пошуку
не записуються. Очікувана OSError фіксується як error та request зі статусом
500. Автоматичні тести перевіряють ці записи й rollback.

Артефакти: logs/lab5-final-tests.txt, lab5-junit.xml, lab5-coverage.json,
lab5-coverage.txt, lab5-performance.json, lab5-verification.json.
Автодемо перевірено; результат у logs/lab5-demo.txt.'''),
('5. Валідація, обмеження та запуск', '''Підсумковий Gate: REVISE, бо людина ще не перевірила відповідність задуму
і не підписала контрольні точки. Автоматична верифікація сервера PASS.
Не виконано UI-перевірку REQ-NF-002 «до 3 кліків» та візуальну частину
REQ-F-007. API повертає дані картки, але це не доводить зручність інтерфейсу.
Докладний сценарій: docs/lab5-human-validation.md.

Запуск у PowerShell із кореня проєкту:
.\\lab5.ps1 test - залежності тестів, регресія, OpenAPI, coverage, SLA.
.\\lab5.ps1 demo - ізольована HTTP-демонстрація без зміни робочих даних.
.\\lab5.ps1 serve - локальний API на 127.0.0.1:8000; Ctrl+C для зупинки.
.\\lab5.ps1 report - відтворення цього PDF з фактичних результатів.

Стан: data/catalog.json. Аудит: logs/runtime/api.jsonl.
Під час зупиненого сервера можна копіювати JSON для резервування/експорту
і відновлювати власну сумісну копію для імпорту. Паралельні процеси з одним
файлом не підтримуються. Це локальний навчальний сервер без авторизації.
Первинне встановлення тестових або PDF-бібліотек потребує інтернету.

Ризики: корельовані помилки агента, розбіжність тестів з потребою,
залежність вимірювань від обладнання. Контроль: контракт як незалежний
артефакт, RED до коду, fault injection, незмінні регресійні тести та
обов'язкова подальша оцінка студентом.

Перевірив(ла): __________________ Дата: __________
Рішення людини: GO / REVISE / STOP __________
Примітки: __________________________________________'''),
('6. Контрольні питання та висновки', Path('docs/lab5-form-answers.md').read_text(encoding='utf-8')),
('7. Історія та простежуваність', '''Основні етапи збережено окремими комітами у фактичному порядку.
Наведений нижче знімок історії отримано командою git log під час генерації:

''' + history + '''
Повна матриця: spec/traceability-matrix.md. План: docs/lab5-plan.md.
Тікети та залишкові перевірки: logs/lab5-final-gate.md.
Вхідні джерела: PDF завдання (11 сторінок), spec/srs.md,
spec/bdd-scenarios.md, spec/glossary.md, docs/api-clarifications.md,
logs/api-gate.md, docs/sdd-backlog.md, docs/risk-register.md.

Звіт згенеровано з поточних результатів. Форма Google не надсилалася;
відеозахист не записувався; твердження про людську валідацію відсутнє.''')
]
Path('docs/lab5-report.md').write_text('\n\n'.join('# '+title+'\n\n'+body for title,body in sections),encoding='utf-8')
font_candidates = [Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/arial.ttf',
                   Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
font = next((p for p in font_candidates if p.exists()),None)
if font is None:
    raise RuntimeError('A Unicode font is required (Arial or DejaVu Sans).')
pdfmetrics.registerFont(TTFont('LabFont',str(font)))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='LabTitle',fontName='LabFont',fontSize=18,leading=24,
                          textColor=colors.HexColor('#17334d'),spaceAfter=18))
styles.add(ParagraphStyle(name='LabText',fontName='LabFont',fontSize=10.5,leading=15,
                          spaceAfter=9))
story=[]
for i,(title,body) in enumerate(sections):
    if i:
        story.append(PageBreak())
    story.append(Paragraph(escape(title),styles['LabTitle']))
    for block in body.split('\n\n'):
        block = re.sub(r'^#+\s*','',block.strip(),flags=re.M)
        if block:
            story.append(Paragraph(escape(block).replace('\n','<br/>'),styles['LabText']))

output = ROOT/'output/pdf/lab5-report.pdf'
output.parent.mkdir(parents=True,exist_ok=True)

def footer(canvas,doc):
    canvas.setFont('LabFont',8)
    canvas.setFillColor(colors.HexColor('#607080'))
    canvas.drawString(42,25,'ЛР5 | SDD + TDD | Андрій Волошин | КН-31')
    canvas.drawRightString(A4[0]-42,25,str(doc.page))

SimpleDocTemplate(str(output),pagesize=A4,rightMargin=42,leftMargin=42,
                  topMargin=42,bottomMargin=45,title='Лабораторна робота 5',
                  author='Андрій Волошин / Codex').build(story,onFirstPage=footer,onLaterPages=footer)
print(output)
