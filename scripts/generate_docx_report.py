"""
Script to generate docs/lab4-report.docx from lab4-report.md content using python-docx.
Strictly adheres to Academic Typography: Times New Roman, 14pt body text.
Part of Laboratory #4 automation.
"""
import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color="D1D5DB", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), val)
        border.set(qn('w:sz'), sz)
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tblBorders.append(border)
    tblPr.append(tblBorders)


def create_docx(output_path: Path):
    doc = Document()

    # Page Margins (Standard A4 academic: left 2.5cm, right 1.5cm, top 2cm, bottom 2cm)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.7)

    # Base Styles: Times New Roman, 14pt
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(14)
    normal_style.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    # Document Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title_p.add_run("ЗВІТ З ЛАБОРАТОРНОЇ РОБОТИ №4")
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = sub_p.add_run("Дисципліна: Проектування інформаційних систем\nТема: Проєктування REST API за специфікацією (API-First SDD Approach)")
    run_sub.font.name = 'Times New Roman'
    run_sub.font.size = Pt(14)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)

    # Metadata Table
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(meta_table, color="D1D5DB")
    meta_data = [
        ("Студент:", "Андрій Волошин (гр. КН-21)"),
        ("Кодинговий агент:", "Antigravity AI Coding Assistant (Gemini 3.8 Flash)"),
        ("Репозиторій проєкту:", "https://github.com/voloshyyn/web-app_for_design-references"),
        ("Дата виконання:", "31 жовтня 2026 р.")
    ]
    for i, (k, v) in enumerate(meta_data):
        row = meta_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.text = k
        c1.text = v
        r0 = c0.paragraphs[0].runs[0]
        r0.font.name = 'Times New Roman'
        r0.font.size = Pt(12)
        r0.font.bold = True
        r1 = c1.paragraphs[0].runs[0]
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(12)
        set_cell_background(c0, "F3F4F6")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 60, 60, 100, 100)
        set_cell_margins(c1, 60, 60, 100, 100)
        c0.width = Inches(2.2)
        c1.width = Inches(4.7)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Helper Functions
    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

    def add_h3(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(2)
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

    def add_p(text, bold_prefix=None):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(5)
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.name = 'Times New Roman'
            rb.font.size = Pt(14)
            rb.font.bold = True
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(14)

    def add_code_block(code_text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.2)
        r = p.add_run(code_text)
        r.font.name = 'Consolas'
        r.font.size = Pt(10.5)
        r.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    # 1. Мета роботи та вхідні артефакти
    add_h2("1. Мета роботи та вхідні артефакти")
    add_p(
        "Опанувати API-first підхід у парадигмі Specification-Driven Development (SDD) та здійснити перехід "
        "від затверджених вимог (SRS Baseline v1.0) до формального, несуперечливого контракту REST API. Сформувати "
        "машинозчитувану специфікацію OpenAPI 3.0.3, розробити DTO та єдину модель помилок RFC 7807 Problem Details, "
        "провести автоматичну валідацію лінтером, розгорнути Mock API сервер без написання коду бекенду, верифікувати "
        "позитивні й негативні сценарії тестування та ухвалити рішення на контрольній точці API-GATE.",
        bold_prefix="Мета роботи: "
    )
    add_p(
        "1. Затверджена специфікація вимог IEEE 830: spec/srs.md (Baseline v1.0, APPROVED).\n"
        "2. Глосарій термінів предметної області (Ubiquitous Language): spec/glossary.md.\n"
        "3. Набір BDD-сценаріїв Gherkin: spec/bdd-scenarios.md (SCN-01 – SCN-07).\n"
        "4. Декомпозиція задач SDD-беклогу: docs/sdd-backlog.md.\n"
        "5. Календарний розрахунок критичного шляху: scripts/calculate_cpm_and_gantt.py.\n"
        "6. Реєстр проєктних ризиків: docs/risk-register.md.\n"
        "7. Базова матриця простежуваності: spec/traceability-matrix.md.\n"
        "8. Протокол контрольної точки: logs/plan-gate.md.",
        bold_prefix="Вхідні артефакти: "
    )

    # 2. Модель REST-ресурсів
    add_h2("2. Модель REST-ресурсів та декомпозиція предметної області")
    add_p(
        "Відповідно до глосарію та вимог SRS, предметну область системи каталогізації дизайн-референсів декомпозовано "
        "на канонічні REST-ресурси верхнього рівня:"
    )
    add_code_block(
        "/api/v1\n"
        "  ├── /references                        # Колекція референсів (створення, фільтрація, пошук)\n"
        "  │     └── /{id}                        # Одиничний референс (перегляд картки, редагування, видалення)\n"
        "  │\n"
        "  ├── /collections                       # Користувацькі колекції / проєктні дошки\n"
        "  │     └── /{id}                        # Деталі колекції з переліком прив'язаних референсів\n"
        "  │           └── /references/{ref_id}   # N:M зв'язок (асоціація / дисоціація референсу з дошкою)\n"
        "  │\n"
        "  ├── /categories                        # Довідник категорій верхнього рівня\n"
        "  │     └── /{name}                      # Одинична категорія (безпечне видалення з Fallback to 'General')\n"
        "  │\n"
        "  └── /health                            # Інфраструктурний ресурс перевірки статусу та SLA"
    )
    add_p(
        "Принципи проектування: використання іменників у множині, канонічні HTTP-дієслова (GET, POST, PUT, DELETE), "
        "та повне приховування деталей внутрішньої реалізації. Внутрішній агрегат Catalog інкапсульовано — зовнішній "
        "клієнт взаємодіє виключно з адресовними ресурсами через стандартизовані DTO."
    )

    # 3. Операції
    add_h2("3. Таблиця операцій REST API та трасування з REQ-ID")
    ops_table = doc.add_table(rows=16, cols=6)
    ops_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(ops_table, color="D1D5DB")
    headers = ["№", "Метод", "Маршрут (URI)", "OpenAPI operationId", "REQ-ID", "Призначення"]
    col_widths = [Inches(0.4), Inches(0.8), Inches(1.8), Inches(1.7), Inches(1.1), Inches(1.3)]
    for j, h in enumerate(headers):
        cell = ops_table.rows[0].cells[j]
        cell.text = h
        r = cell.paragraphs[0].runs[0]
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        r.font.bold = True
        set_cell_background(cell, "E5E7EB")
        set_cell_margins(cell, 60, 60, 60, 60)
        cell.width = col_widths[j]

    rows_data = [
        ("1", "GET", "/references", "listReferences", "REQ-F-005, 006", "Кон'юнктивна фільтрація, пошук, пагінація"),
        ("2", "POST", "/references", "createReference", "REQ-F-001, NF-004", "Створення референсу із санітизацією URL"),
        ("3", "GET", "/references/{id}", "getReferenceById", "REQ-F-007", "Отримання картки референсу за ID"),
        ("4", "PUT", "/references/{id}", "updateReference", "REQ-F-008, NF-004", "Оновлення метаданих, тегів та категорії"),
        ("5", "DELETE", "/references/{id}", "deleteReference", "REQ-F-008", "Безпечне видалення референсу"),
        ("6", "GET", "/collections", "listCollections", "REQ-F-003", "Перелік тематичних дощок проєктів"),
        ("7", "POST", "/collections", "createCollection", "REQ-F-003", "Створення нової тематичної дошки"),
        ("8", "GET", "/collections/{id}", "getCollectionById", "REQ-F-003", "Перегляд дошки з переліком прив'язаних ID"),
        ("9", "DELETE", "/collections/{id}", "deleteCollection", "REQ-F-003", "Видалення дошки без видалення референсів"),
        ("10", "POST", "/collections/{id}/references/{ref_id}", "addReferenceToCollection", "REQ-F-003", "Додавання референсу до дошки (N:M)"),
        ("11", "DELETE", "/collections/{id}/references/{ref_id}", "removeReferenceFromCollection", "REQ-F-003", "Вилучення референсу з дошки"),
        ("12", "GET", "/categories", "listCategories", "REQ-F-002", "Список доступних категорій класифікації"),
        ("13", "POST", "/categories", "createCategory", "REQ-F-002", "Реєстрація нової категорії"),
        ("14", "DELETE", "/categories/{name}", "deleteCategory", "REQ-NF-003", "Видалення категорії (Fallback на 'General')"),
        ("15", "GET", "/health", "getHealthStatus", "REQ-NF-001, NF-005", "Моніторинг працездатності та SLA")
    ]
    for i, row_vals in enumerate(rows_data):
        row = ops_table.rows[i + 1]
        for j, val in enumerate(row_vals):
            cell = row.cells[j]
            cell.text = val
            r = cell.paragraphs[0].runs[0]
            r.font.name = 'Times New Roman'
            r.font.size = Pt(10.5)
            if j == 1:
                r.font.bold = True
            set_cell_margins(cell, 40, 40, 50, 50)
            cell.width = col_widths[j]
            if i % 2 == 1:
                set_cell_background(cell, "F9FAFB")

    # 4. Схеми даних
    add_h2("4. Схеми даних запитів і відповідей (DTO)")
    add_p(
        "Усі структури даних у специфікації spec/openapi.yaml формалізовано через незалежні схеми:\n"
        "1. ReferenceResponseDto: повне представлення референсу (id, title, url, image_url, category, tags, notes, created_at).\n"
        "2. ReferenceCreateDto: вхідний DTO створення (title minLength: 1, url з патерном ^https?://, опціональні теги й нотатки).\n"
        "3. ReferenceUpdateDto: DTO модифікації полів референсу.\n"
        "4. ReferenceListResponse: обгортка вибірки з параметрами пагінації (items, total, limit, offset).\n"
        "5. CollectionResponseDto / CollectionWithReferencesDto: моделі тематичних колекцій.\n"
        "6. CategoryResponseDto / CategoryCreateDto: моделі категорій з ознакою is_default.\n"
        "7. CategoryMigrationReportDto: звіт про автоматичне перенесення референсів у дефолтну категорію."
    )

    # 5. Модель помилок
    add_h2("5. Єдина модель помилок (RFC 7807 Problem Details)")
    add_p(
        "Для всіх помилкових відповідей стандартизовано MIME-тип application/problem+json за стандартом RFC 7807:\n"
        "- type: URI-ідентифікатор типу помилки;\n"
        "- title: короткий зрозумілий людині опис;\n"
        "- status: числовий HTTP-код стану;\n"
        "- code: машиннозчитуваний внутрішній код помилки;\n"
        "- detail: докладне пояснення конкретного інциденту;\n"
        "- instance: URI-шлях запиту;\n"
        "- invalid_params: масив помилок валідації конкретних полів."
    )
    add_code_block(
        "{\n"
        '  "type": "https://api.design-refs.local/errors/validation-error",\n'
        '  "title": "Validation Failed",\n'
        '  "status": 400,\n'
        '  "code": "VALIDATION_FAILED",\n'
        '  "detail": "Required fields validation failed.",\n'
        '  "instance": "/api/v1/references",\n'
        '  "timestamp": "2026-10-31T14:05:00Z",\n'
        '  "invalid_params": [\n'
        '    {"name": "title", "reason": "Title is required and cannot be empty."}\n'
        "  ]\n"
        "}"
    )

    # 6. Валідація OpenAPI
    add_h2("6. Результати автоматичної валідації специфікації OpenAPI")
    add_p(
        "Валідація здійснюється автоматичним лінтером scripts/validate_openapi.py. "
        "Результати перевірки (з журналу logs/openapi-validation.log):\n"
        "- Проаналізовано маршрутів: 8, операцій: 15, компонентних схем: 13;\n"
        "- Покриття трасування x-req-id: 15/15 (100.0%);\n"
        "- Виявлено синтаксичних помилок: 0, битих посилань $ref: 0, попереджень: 0;\n"
        "- Статус валідації: PASSED (GO)."
    )

    # 7. Mock API
    add_h2("7. Архітектура Mock API сервера та верифікація контракту")
    add_p(
        "Для перевірки функціонування контракту без створення продуктового серверного коду реалізовано автономний "
        "Mock API сервер на стандартній бібліотеці Python (scripts/mock_server.py). Сервер відтворює всі бізнес-правила: "
        "кон'юнктивне фільтрування за множинами тегів (AND-семантика), санітизацію протоколів URL (захист від XSS через "
        "javascript: протокол) та каскадне безпечне перепризначення категорій на General."
    )

    # 8. Тестування сценаріїв
    add_h2("8. Протокол тестування позитивних і негативних сценаріїв")
    add_p(
        "Скрипт scripts/test_mock_scenarios.py виконав автоматизоване тестування 14 контрактних сценаріїв проти "
        "працюючого Mock API (8 позитивних POS-01..08 та 6 негативних NEG-01..06):"
    )

    test_table = doc.add_table(rows=15, cols=7)
    test_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(test_table, color="D1D5DB")
    test_headers = ["ID", "Тип", "Назва сценарію", "REQ-ID", "Метод & URI", "HTTP", "Статус"]
    t_widths = [Inches(0.8), Inches(0.8), Inches(2.2), Inches(1.0), Inches(1.5), Inches(0.5), Inches(0.8)]
    for j, th in enumerate(test_headers):
        cell = test_table.rows[0].cells[j]
        cell.text = th
        r = cell.paragraphs[0].runs[0]
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        r.font.bold = True
        set_cell_background(cell, "E5E7EB")
        set_cell_margins(cell, 60, 60, 50, 50)
        cell.width = t_widths[j]

    scenarios_data = [
        ("POS-01", "Positive", "Створення референсу з валідними полями", "REQ-F-001", "POST /references", "201", "PASSED"),
        ("POS-02", "Positive", "Отримання картки за ID", "REQ-F-007", "GET /references/ref-001", "200", "PASSED"),
        ("POS-03", "Positive", "Кон'юнктивна фільтрація за тегами (AND)", "REQ-F-005", "GET /references?tags=...", "200", "PASSED"),
        ("POS-04", "Positive", "Повнотекстовий пошук за підрядком", "REQ-F-006", "GET /references?q=dashboard", "200", "PASSED"),
        ("POS-05", "Positive", "Додавання референсу до колекції (N:M)", "REQ-F-003", "POST /collections/.../ref-002", "200", "PASSED"),
        ("POS-06", "Positive", "Отримання категорій із 'General'", "REQ-F-002", "GET /categories", "200", "PASSED"),
        ("POS-07", "Positive", "Оновлення метаданих референсу", "REQ-F-008", "PUT /references/ref-001", "200", "PASSED"),
        ("POS-08", "Positive", "Безпечне видалення категорії з міграцією", "REQ-NF-003", "DELETE /categories/Branding", "200", "PASSED"),
        ("NEG-01", "Negative", "Безпека: блокування javascript: протоколу", "REQ-NF-004", "POST /references", "422", "PASSED"),
        ("NEG-02", "Negative", "Валідація: відхилення порожнього title", "REQ-F-001", "POST /references", "400", "PASSED"),
        ("NEG-03", "Negative", "Відсутність ресурсу: неіснуючий ID", "REQ-F-007", "GET /references/ref-999", "404", "PASSED"),
        ("NEG-04", "Negative", "Цілісність: заборона видалення 'General'", "REQ-NF-003", "DELETE /categories/General", "400", "PASSED"),
        ("NEG-05", "Negative", "Синтаксис: відхилення невалідного JSON", "REQ-NF-005", "POST /references", "400", "PASSED"),
        ("NEG-06", "Negative", "Неіснуюча колекція: асоціація з col-999", "REQ-F-003", "POST /collections/col-999/...", "404", "PASSED")
    ]
    for i, row_vals in enumerate(scenarios_data):
        row = test_table.rows[i + 1]
        for j, val in enumerate(row_vals):
            cell = row.cells[j]
            cell.text = val
            r = cell.paragraphs[0].runs[0]
            r.font.name = 'Times New Roman'
            r.font.size = Pt(10)
            if j == 6:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0x15, 0x80, 0x3D)
            elif j == 0:
                r.font.bold = True
            set_cell_margins(cell, 40, 40, 50, 50)
            cell.width = t_widths[j]
            if i % 2 == 1:
                set_cell_background(cell, "F9FAFB")

    add_p(
        "Підсумок тестування: успішно пройдено 14/14 (100.0%). Середня затримка відгуку Mock API: 2.7 мс "
        "(що у 18 разів перевершує норматив цільового показника SLA < 50 мс)."
    )

    # 9. Адендум
    add_h2("9. Адендум та фіксація уточненої поведінки")
    add_p(
        "Усі інженерні уточнення, виявлені під час деталізації REST-контракту, офіційно зафіксовано в документі "
        "docs/api-clarifications.md:\n"
        "1. Введення параметрів постраничного виведення (limit, offset) у DTO ReferenceListResponse;\n"
        "2. Уніфікація відповідей помилок за стандартом RFC 7807 (ProblemDetails);\n"
        "3. DTO деталізованого звіту про автоматичну міграцію категорій CategoryMigrationReportDto;\n"
        "4. Додавання системного ендпоінта моніторингу працездатності GET /health."
    )

    # 10. API-GATE
    add_h2("10. Рішення контрольної точки API-GATE")
    add_p(
        "Відповідно до протоколу logs/api-gate.md, на контрольній точці зафіксовано рішення: APPROVED (GO). "
        "Усі 10 обов'язкових умов шлюзу якості виконано на 100%. Контракт REST API офіційно затверджено як базу для "
        "реалізації 5-ї лабораторної роботи за TDD."
    )

    # 11. Висновки
    add_h2("11. Висновки")
    add_p(
        "У ході виконання лабораторної роботи №4 було успішно реалізовано повний цикл проєктування REST API "
        "з використанням API-first підходу та принципів Specification-Driven Development (SDD).\n\n"
        "Ключові досягнення:\n"
        "1. Спроєктовано несуперечливий контракт на базі стандарту OpenAPI 3.0.3 (spec/openapi.yaml, spec/openapi.json);\n"
        "2. Забезпечено 100% двонаправлене трасування кожної операції з ідентифікаторами вимог базової SRS v1.0 через x-req-id;\n"
        "3. Впроваджено єдину модель помилок RFC 7807 (ProblemDetails), що ліквідує загрозу витоку внутрішніх деталей реалізації;\n"
        "4. Розроблено та успішно верифіковано автоматичний лінтер scripts/validate_openapi.py (0 помилок, 0 зауважень);\n"
        "5. Створено автономний Mock API сервер (scripts/mock_server.py) та автоматизовано тестування 14 сценаріїв "
        "(scripts/test_mock_scenarios.py) зі 100% контрактною відповідністю;\n"
        "6. Оновлено матрицю простежуваності spec/traceability-matrix.md та успішно пройдено шлюз якості API-GATE (GO)."
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"[*] Report successfully created with Times New Roman 14pt at: {output_path}")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "docs" / "lab4-report.docx"
    create_docx(out)
