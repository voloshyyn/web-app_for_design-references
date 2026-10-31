"""
Script to generate docs/lab4-report.docx from lab4-report.md content using python-docx.
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


def create_docx(output_path: Path):
    doc = Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    # Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("Звіт з лабораторної роботи №4")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    run_sub = sub_p.add_run("Дисципліна: Проектування інформаційних систем\nТема: Проєктування REST API за специфікацією (API-First SDD Approach)")
    run_sub.font.size = Pt(12)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(0x3B, 0x82, 0xF6)

    # Metadata box
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Студент:", "Андрій Волошин (гр. КН-21)"),
        ("Кодинговий агент:", "Antigravity AI Coding Assistant (Gemini 3.8 Flash)"),
        ("Репозиторій:", "https://github.com/voloshyyn/web-app_for_design-references"),
        ("Дата виконання:", "31 жовтня 2026 р.")
    ]
    for i, (k, v) in enumerate(meta_data):
        row = meta_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.text = k
        c1.text = v
        c0.paragraphs[0].runs[0].font.bold = True
        set_cell_background(c0, "F3F4F6")
        set_cell_background(c1, "F9FAFB")
        set_cell_margins(c0, 60, 60, 100, 100)
        set_cell_margins(c1, 60, 60, 100, 100)
        c0.width = Inches(1.8)
        c1.width = Inches(5.0)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

    def add_p(text, bold_prefix=None):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.bold = True
        p.add_run(text)

    # 1. Мета роботи
    add_h2("1. Мета роботи та вхідні артефакти")
    add_p(
        "Опанувати API-first підхід у парадигмі Specification-Driven Development (SDD) та здійснити перехід "
        "від затверджених вимог (SRS Baseline v1.0) до формального контракту REST API. Сформувати машинозчитувану "
        "специфікацію OpenAPI 3.0.3, провести її автоматичну валідацію, розгорнути Mock API без створення серверного коду, "
        "верифікувати позитивні й негативні сценарії та ухвалити рішення на контрольній точці API-GATE.",
        bold_prefix="Мета: "
    )
    add_p(
        "Затверджена специфікація SRS v1.0, глосарій термінів (spec/glossary.md), набір BDD-сценаріїв (spec/bdd-scenarios.md), "
        "SDD-беклог та матриця простежуваності з ЛР2 і ЛР3.",
        bold_prefix="Вхідні артефакти: "
    )

    # 2. Модель REST-ресурсів
    add_h2("2. Модель REST-ресурсів та декомпозиція")
    add_p("Предметну область декомпозовано на ресурси: /references (основний каталог), /collections (проєктні дошки), /categories (взаємовиключна класифікація) та /health (системний моніторинг). Всі ресурси використовують іменники у множині та канонічні методи HTTP (GET, POST, PUT, DELETE). Деталі внутрішньої реалізації (клас Catalog) надійно інкапсульовані.")

    # 3. Операції
    add_h2("3. Операції REST API та зв'язок з REQ-ID")
    ops_table = doc.add_table(rows=16, cols=5)
    ops_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["№", "Метод", "Маршрут URI", "OpenAPI operationId", "REQ-ID"]
    for j, h in enumerate(headers):
        cell = ops_table.rows[0].cells[j]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_background(cell, "E5E7EB")
        set_cell_margins(cell, 60, 60, 80, 80)

    rows_data = [
        ("1", "GET", "/references", "listReferences", "REQ-F-005, 006"),
        ("2", "POST", "/references", "createReference", "REQ-F-001, NF-004"),
        ("3", "GET", "/references/{id}", "getReferenceById", "REQ-F-007"),
        ("4", "PUT", "/references/{id}", "updateReference", "REQ-F-008, NF-004"),
        ("5", "DELETE", "/references/{id}", "deleteReference", "REQ-F-008"),
        ("6", "GET", "/collections", "listCollections", "REQ-F-003"),
        ("7", "POST", "/collections", "createCollection", "REQ-F-003"),
        ("8", "GET", "/collections/{id}", "getCollectionById", "REQ-F-003"),
        ("9", "DELETE", "/collections/{id}", "deleteCollection", "REQ-F-003"),
        ("10", "POST", "/collections/{id}/references/{ref_id}", "addReferenceToCollection", "REQ-F-003"),
        ("11", "DELETE", "/collections/{id}/references/{ref_id}", "removeReferenceFromCollection", "REQ-F-003"),
        ("12", "GET", "/categories", "listCategories", "REQ-F-002"),
        ("13", "POST", "/categories", "createCategory", "REQ-F-002"),
        ("14", "DELETE", "/categories/{name}", "deleteCategory", "REQ-NF-003"),
        ("15", "GET", "/health", "getHealthStatus", "REQ-NF-001, NF-005")
    ]
    for i, row_vals in enumerate(rows_data):
        row = ops_table.rows[i + 1]
        for j, val in enumerate(row_vals):
            cell = row.cells[j]
            cell.text = val
            set_cell_margins(cell, 40, 40, 60, 60)
            if i % 2 == 1:
                set_cell_background(cell, "F9FAFB")

    # 4. Єдина модель помилок
    add_h2("4. Єдина модель помилок (RFC 7807 Problem Details)")
    add_p("Всі помилкові HTTP-відповіді стандартизовано за міжнародним стандартом RFC 7807 (Problem Details). Структура включає атрибути type, title, status, code, detail, instance, timestamp та масив некоректних полів invalid_params для сценаріїв 400 і 422.")

    # 5. Результати валідації
    add_h2("5. Автоматична валідація специфікації OpenAPI")
    add_p("Специфікація spec/openapi.yaml перевірена автоматичним лінтером scripts/validate_openapi.py. Результат: 15/15 операцій трасовані до REQ-ID (100%), 0 синтаксичних помилок, 0 порушених посилань $ref, 0 попереджень. Статус: PASSED (GO).")

    # 6. Mock API та сценарії
    add_h2("6. Mock API та результати тестування 14 сценаріїв")
    add_p("Розгорнуто автономний Mock API сервер (scripts/mock_server.py). Скрипт scripts/test_mock_scenarios.py виконав 14 сценаріїв (8 позитивних POS-01..08 та 6 негативних NEG-01..06). Результат: 14/14 PASSED (100%), середня затримка відгуку 2.7 мс (SLA < 50 мс перевиконано в 18 разів).")

    # 7. Рішення API-GATE
    add_h2("7. Рішення контрольної точки API-GATE")
    add_p("Усі 10 критеріїв шлюзу якості виконано на 100%. Підписано офіційний протокол logs/api-gate.md. Вердикт: APPROVED (GO). Затверджено базову лінію контракту REST API v1.0 та відкрито доступ до реалізації за методикою TDD у ЛР5.")

    # 8. Висновки
    add_h2("8. Висновки")
    add_p("У ході лабораторної роботи №4 опановано API-first підхід у SDD. Розроблено та валідовано OpenAPI 3.0.3 специфікацію, уніфіковано модель помилок за RFC 7807, забезпечено нульову втрату даних при міграції категорій, сформовано адендум на пагінацію (docs/api-clarifications.md) та доведено 100% контрактну відповідність через Mock API.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"[*] Report saved successfully to: {output_path}")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "docs" / "lab4-report.docx"
    create_docx(out)
