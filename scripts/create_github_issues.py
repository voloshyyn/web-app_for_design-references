"""
Automated GitHub Issues and Labels Creator for SDD Project.
Uses Python Standard Library (urllib) - zero external dependencies.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error

REPO = "voloshyyn/web-app_for_design-references"

LABELS = [
    {"name": "type:specification", "color": "d4c5f9", "description": "Вимоги, межі, бізнес-правила"},
    {"name": "type:gate", "color": "b60205", "description": "Контрольна точка Stage-Gate (Human Only)"},
    {"name": "type:test", "color": "0e8a16", "description": "BDD/TDD тести (Test-First)"},
    {"name": "type:feature", "color": "1d76db", "description": "Імплементація функціонального коду"},
    {"name": "type:verification", "color": "fbca04", "description": "Автоматизовані тести, лінтинг, SLA"},
    {"name": "type:validation", "color": "006b75", "description": "Людська валідація UX та задуму"},
    {"name": "type:documentation", "color": "c2e0c6", "description": "Документація, матриця RTM"},
    {"name": "role:human", "color": "5319e7", "description": "Виконує або затверджує людина"},
    {"name": "role:ai-agent", "color": "0052cc", "description": "Виконує ШІ-кодинговий агент"},
    {"name": "role:joint", "color": "bfdadc", "description": "Спільне виконання (Людина + ШІ)"},
    {"name": "role:ci", "color": "ededed", "description": "Автоматизований CI конвеєр"},
    {"name": "priority:critical", "color": "e11d21", "description": "Критичний пріоритет (Критичний шлях)"},
    {"name": "priority:high", "color": "eb6420", "description": "Високий пріоритет"},
    {"name": "priority:standard", "color": "cccccc", "description": "Стандартний пріоритет"},
    {"name": "high-cost-of-failure", "color": "b60205", "description": "Висока ціна відмови (Безпека / Цілісність)"},
]

TASKS = [
    {
        "id": "SPEC-BASE",
        "title": "[SPEC-BASE] Аудит базової лінії SRS v1.0 та верифікація меж",
        "req": "REQ-F-001..008, REQ-NF-001..005",
        "type": "Specification",
        "role": "Human",
        "ai_h": 0.2,
        "human_h": 1.0,
        "preds": "— (Коренева задача)",
        "notes": "Людина верифікує відсутність прогалин перед початком робіт",
        "labels": ["type:specification", "role:human", "priority:standard"]
    },
    {
        "id": "GATE-PLAN",
        "title": "[GATE-PLAN] Контрольна точка PLAN-GATE (Рішення GO)",
        "req": "Всі вимоги (ALL)",
        "type": "Gate",
        "role": "Human",
        "ai_h": 0.1,
        "human_h": 0.5,
        "preds": "SPEC-BASE",
        "notes": "Бінарне рішення GO/REVISE. Дозвіл на початок розробки. ШІ заборонено приймати рішення.",
        "labels": ["type:gate", "role:human", "priority:critical"]
    },
    {
        "id": "TEST-01",
        "title": "[TEST-01] Розробка BDD-тестів створення та валідації URL (SCN-01, SCN-02)",
        "req": "REQ-F-001, REQ-NF-004",
        "type": "Test",
        "role": "Joint",
        "ai_h": 0.3,
        "human_h": 0.7,
        "preds": "GATE-PLAN",
        "notes": "ШІ пише тест, Людина перевіряє сценарії блокування javascript: та XSS (Висока ціна відмови)",
        "labels": ["type:test", "role:joint", "priority:critical", "high-cost-of-failure"]
    },
    {
        "id": "FEAT-01",
        "title": "[FEAT-01] Імплементація сутності Reference та валідатора URL/XSS",
        "req": "REQ-F-001, REQ-NF-004",
        "type": "Feature",
        "role": "AI Agent",
        "ai_h": 0.5,
        "human_h": 0.2,
        "preds": "TEST-01",
        "notes": "Блокується до створення та схвалення TEST-01 (Принцип TDD-блокування)",
        "labels": ["type:feature", "role:ai-agent", "priority:critical", "high-cost-of-failure"]
    },
    {
        "id": "TEST-02",
        "title": "[TEST-02] Розробка тестів категорій та Fallback до 'General' (SCN-05)",
        "req": "REQ-F-002, REQ-NF-003",
        "type": "Test",
        "role": "AI Agent",
        "ai_h": 0.2,
        "human_h": 0.3,
        "preds": "TEST-01",
        "notes": "Перевірка 0% втрати даних при видаленні категорії (Fallback to General)",
        "labels": ["type:test", "role:ai-agent", "priority:critical", "high-cost-of-failure"]
    },
    {
        "id": "FEAT-02",
        "title": "[FEAT-02] Реалізація категорій та механізму цілісності",
        "req": "REQ-F-002, REQ-NF-003",
        "type": "Feature",
        "role": "AI Agent",
        "ai_h": 0.4,
        "human_h": 0.2,
        "preds": "FEAT-01, TEST-02",
        "notes": "Прив'язка до дефолтної категорії General при видаленні",
        "labels": ["type:feature", "role:ai-agent", "priority:critical"]
    },
    {
        "id": "GATE-CORE",
        "title": "[GATE-CORE] Контрольна точка CORE-GATE (Перевірка ядра та безпеки)",
        "req": "REQ-F-001, REQ-F-002, REQ-NF-003, REQ-NF-004",
        "type": "Gate",
        "role": "Human",
        "ai_h": 0.1,
        "human_h": 0.8,
        "preds": "FEAT-02",
        "notes": "Аудит людиною захисту від ін'єкцій та цілісності даних перед стартом 2-го спринту",
        "labels": ["type:gate", "role:human", "priority:critical", "high-cost-of-failure"]
    },
    {
        "id": "TEST-03",
        "title": "[TEST-03] Тести фасетного тегування та AND-фільтрації (SCN-03, SCN-04)",
        "req": "REQ-F-004, REQ-F-005, REQ-NF-001",
        "type": "Test",
        "role": "AI Agent",
        "ai_h": 0.3,
        "human_h": 0.3,
        "preds": "GATE-CORE",
        "notes": "Перевірка префіксів namespace:value та SLA швидкодії пошуку < 50 мс",
        "labels": ["type:test", "role:ai-agent", "priority:standard"]
    },
    {
        "id": "FEAT-03",
        "title": "[FEAT-03] Імплементація нормалізації тегів та фасетного індексатора",
        "req": "REQ-F-004, REQ-F-005",
        "type": "Feature",
        "role": "AI Agent",
        "ai_h": 0.6,
        "human_h": 0.2,
        "preds": "TEST-03",
        "notes": "Реалізація перетину множин тегів у Catalog.filter_by_tags",
        "labels": ["type:feature", "role:ai-agent", "priority:standard"]
    },
    {
        "id": "TEST-04",
        "title": "[TEST-04] Тести повнотекстового пошуку (SCN-06) та колекцій N:M (SCN-07)",
        "req": "REQ-F-003, REQ-F-006, REQ-F-007, REQ-F-008",
        "type": "Test",
        "role": "AI Agent",
        "ai_h": 0.3,
        "human_h": 0.3,
        "preds": "TEST-03",
        "notes": "Пошук за підрядками без урахування регістру та зв'язки колекцій",
        "labels": ["type:test", "role:ai-agent", "priority:standard"]
    },
    {
        "id": "FEAT-04",
        "title": "[FEAT-04] Імплементація пошуку, колекцій та операцій CRUD",
        "req": "REQ-F-003, REQ-F-006, REQ-F-007, REQ-F-008",
        "type": "Feature",
        "role": "AI Agent",
        "ai_h": 0.7,
        "human_h": 0.2,
        "preds": "FEAT-03, TEST-04",
        "notes": "Пошук у Catalog.search, моделі Collection та каскадне очищення при видаленні",
        "labels": ["type:feature", "role:ai-agent", "priority:standard"]
    },
    {
        "id": "VERIF-ALL",
        "title": "[VERIF-ALL] Автоматизована верифікація та бенчмарк SLA (CI Suite)",
        "req": "REQ-NF-001, REQ-NF-005",
        "type": "Verification",
        "role": "Automated / CI",
        "ai_h": 0.3,
        "human_h": 0.2,
        "preds": "FEAT-04",
        "notes": "100% проходження pytest, контроль стилю PEP 8 та Latency SLA < 50 мс",
        "labels": ["type:verification", "role:ci", "priority:standard"]
    },
    {
        "id": "VALID-UX",
        "title": "[VALID-UX] Валідація людиною (UX audit, відповідність концепції)",
        "req": "REQ-NF-002",
        "type": "Validation",
        "role": "Human",
        "ai_h": 0.1,
        "human_h": 1.0,
        "preds": "VERIF-ALL",
        "notes": "Перевірка додавання референсу за <= 3 кроки, ергономіка, відсутність gold plating",
        "labels": ["type:validation", "role:human", "priority:high"]
    },
    {
        "id": "DOC-RTM",
        "title": "[DOC-RTM] Фіналізація документації та матриці RTM",
        "req": "Всі вимоги (ALL)",
        "type": "Documentation",
        "role": "Joint",
        "ai_h": 0.4,
        "human_h": 0.6,
        "preds": "VALID-UX",
        "notes": "Синхронізація traceability-matrix.md, sdd-backlog.md та звітів",
        "labels": ["type:documentation", "role:joint", "priority:standard"]
    },
    {
        "id": "GATE-FINAL",
        "title": "[GATE-FINAL] Контрольна точка RELEASE-GATE (Фінальне схвалення)",
        "req": "Всі вимоги (ALL)",
        "type": "Gate",
        "role": "Human",
        "ai_h": 0.1,
        "human_h": 0.5,
        "preds": "DOC-RTM",
        "notes": "Остаточний допуск релізу до влиття в main. Рішення належить виключно людині.",
        "labels": ["type:gate", "role:human", "priority:critical"]
    }
]


def send_github_request(url: str, token: str, data: dict = None) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data else None,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SDD-Python-Creator",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        if e.code == 422 and "already_exists" in error_body:
            return {"status": "already_exists"}
        raise RuntimeError(f"HTTP {e.code}: {error_body}")


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1]
    if not token:
        token = input("Введіть ваш GitHub Personal Access Token (PAT): ").strip()
    if not token:
        print("Помилка: токен не вказано.")
        sys.exit(1)

    print(f"=== 1. Створення/оновлення міток для {REPO} ===")
    for lbl in LABELS:
        url = f"https://api.github.com/repos/{REPO}/labels"
        try:
            res = send_github_request(url, token, lbl)
            print(f" [+] Мітка: {lbl['name']}")
        except Exception as e:
            print(f" [=] Пропущено або помилка для {lbl['name']}: {e}")

    print(f"\n=== 2. Створення 15 SDD-тікетів для {REPO} ===")
    created = 0
    for task in TASKS:
        total_h = round(task["ai_h"] + task["human_h"], 2)
        body = (
            f"### 📋 Опис задачі (SDD Task ID: {task['id']})\n"
            f"{task['notes']}\n\n"
            f"---\n\n"
            f"### 🔗 Зв'язок зі специфікацією (Traceability)\n"
            f"- **Вимоги SRS:** `{task['req']}`\n"
            f"- **Тип тікета:** `{task['type']}`\n"
            f"- **Попередники в графі (Predecessors):** `{task['preds']}`\n\n"
            f"---\n\n"
            f"### 👥 Розподіл ролей та трудовитрати\n"
            f"- **Основний виконавець:** `{task['role']}`\n"
            f"- **Оцінка часу ШІ-агента:** {task['ai_h']} год\n"
            f"- **Оцінка часу інженера (людини):** {task['human_h']} год\n"
            f"- **Сумарна тривалість:** {total_h} год\n\n"
            f"---\n\n"
            f"### 🛡️ Інженерні правила виконання\n"
            f"- **TDD-блокування:** Якщо це задача типу `Feature`, кодування дозволено лише після успішного затвердження відповідного тікета `Test`.\n"
            f"- **Суверенітет Gate:** Якщо це `Gate`, рішення ухвалюється виключно інженером-людиною (статус APPROVED або REVISE).\n"
        )

        payload = {
            "title": task["title"],
            "body": body,
            "labels": task["labels"]
        }
        url = f"https://api.github.com/repos/{REPO}/issues"
        try:
            resp = send_github_request(url, token, payload)
            print(f" [✔] Створено Issue #{resp.get('number')}: {task['title']}")
            created += 1
            time.sleep(0.5)
        except Exception as e:
            print(f" [✖] Помилка створення {task['id']}: {e}")

    print(f"\n=== Успішно створено {created} з 15 тікетів у {REPO}! ===")


if __name__ == "__main__":
    main()
