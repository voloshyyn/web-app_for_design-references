# Початкова матриця простежуваності вимог (Requirements Traceability Matrix, RTM)

- **Проєкт:** Система каталогізації та швидкого пошуку дизайн-референсів (`web-app_for_design-references`)
- **Етап SDLC:** Завершення фази специфікації вимог (Лабораторна робота №2, перед проходженням SPEC-GATE)
- **Призначення:** Забезпечення наскрізної двонаправленої простежуваності між вимогами, критеріями прийняття, BDD-сценаріями та майбутніми артефактами реалізації (тікети, модульні тести, код, призначена для користувача документація).

---

## 1. Матриця функціональних вимог (Functional Requirements Traceability)

| ID Вимоги | Короткий опис вимоги | Критерій прийняття (AC) | BDD-сценарій | Тікет (Task ID) | Модульний тест (Test ID) | Реалізація в коді (Code Unit) | Документація (Doc Ref) |
|---|---|---|---|---|---|---|---|
| **REQ-F-001** | Створення референсу із зовнішнього джерела (URL, назва, картинка) | `AC-F-001.1` (Успішне створення)<br>`AC-F-001.2` (Валідація обов'язкових полів) | `SCN-01`<br>`SCN-02` | `[TASK-01]` | `tests/test_bdd_scenarios.py::test_create_reference_success`<br>`::test_create_reference_invalid_url` | `src/models.py::Reference` | `docs/user-guide.md#creating-reference` |
| **REQ-F-002** | Асоціація референсу з категорією (1:1) | `AC-F-002.1` (Прив'язка категорії)<br>`AC-F-002.2` (Дефолтна категорія "General") | `SCN-01`<br>`SCN-05` | `[TASK-02]` | `tests/test_bdd_scenarios.py::test_category_assignment` | `src/models.py::Reference.category` | `docs/user-guide.md#categories` |
| **REQ-F-003** | Групування референсів у колекції (N:M) | `AC-F-003.1` (Додавання до багатьох колекцій) | — | `[TASK-03]` | `tests/test_bdd_scenarios.py::test_collection_mapping` | `src/models.py::Collection` | `docs/user-guide.md#collections` |
| **REQ-F-004** | Управління тегами та фасетами | `AC-F-004.1` (Нормалізація тегів до нижнього регістру)<br>`AC-F-004.2` (Підтримка префіксів `namespace:val`) | `SCN-01`<br>`SCN-04` | `[TASK-04]` | `tests/test_bdd_scenarios.py::test_tag_management_and_facets` | `src/models.py::Reference.add_tag` | `docs/user-guide.md#tagging` |
| **REQ-F-005** | Миттєва кон'юнктивна фільтрація за тегами (AND) | `AC-F-005.1` (Перетин множин тегів)<br>`AC-F-005.2` (Фільтрація за фасетами) | `SCN-03`<br>`SCN-04` | `[TASK-05]` | `tests/test_bdd_scenarios.py::test_conjunctive_tag_filtering` | `src/models.py::Catalog.filter_by_tags` | `docs/user-guide.md#filtering` |
| **REQ-F-006** | Повнотекстовий пошук за назвою, нотатками та тегами | `AC-F-006.1` (Пошук без урахування регістру) | `SCN-06` | `[TASK-06]` | `tests/test_bdd_scenarios.py::test_full_text_search` | `src/models.py::Catalog.search` | `docs/user-guide.md#search` |
| **REQ-F-007** | Перегляд детальної картки референсу з прев'ю | `AC-F-007.1` (Відображення всіх атрибутів та прев'ю) | — | `[TASK-07]` | `tests/test_smoke.py` | `src/models.py::Reference` | `docs/user-guide.md#reference-card` |
| **REQ-F-008** | Редагування та видалення референсу | `AC-F-008.1` (Оновлення метаданих)<br>`AC-F-008.2` (Видалення без залишкових зв'язків) | `SCN-05` | `[TASK-08]` | `tests/test_bdd_scenarios.py::test_delete_reference` | `src/models.py::Catalog.remove_reference` | `docs/user-guide.md#managing-items` |

---

## 2. Матриця нефункціональних вимог (Non-Functional Requirements Traceability)

| ID Вимоги | Категорія вимоги | Критерій прийняття (AC) | BDD-сценарій | Метод верифікації | Цільовий метричний показник |
|---|---|---|---|---|---|
| **REQ-NF-001** | Швидкодія (Performance) | `AC-NF-001.1` | `SCN-03` | Автоматизований бенчмарк-тест часу виконання | Latency < 50 мс для каталогу з 1000 референсів |
| **REQ-NF-002** | Зручність використання (Usability) | `AC-NF-002.1` | `SCN-01` | Аудит інтерфейсу (GOMS / KLM-аналіз дій) | Додавання референсу з 3 тегами за ≤ 3 дії/кліки |
| **REQ-NF-003** | Надійність та цілісність (Reliability) | `AC-NF-003.1` | `SCN-05` | Інтеграційні тести цілісності зв'язків моделей | 0% втрати даних при видаленні пов'язаних категорій (автопереведення в General) |
| **REQ-NF-004** | Безпека (Security) | `AC-NF-004.1` | `SCN-02` | Тестування валідації вхідних даних (Fuzzing / Injection tests) | 100% блокування небезпечних протоколів (`javascript:`, `data:`) та екранування тексту |
| **REQ-NF-005** | Супровідність (Maintainability) | `AC-NF-005.1` | — | Статичний аналіз коду та аналіз покриття (Coverage) | 100% покриття бізнес-правил моделі модульними тестами, відповідність PEP 8 |

---

## 3. Резюме простежуваності

- **Загальна кількість вимог:** 13 (8 функціональних, 5 нефункціональних).
- **Покриття критеріями прийняття (AC):** 100% вимог мають формалізовані та вимірні критерії прийняття.
- **Покриття поведінковими BDD-сценаріями:** Усі критичні призначені для користувача потоки (Happy Path, валідаційні границі, кон'юнктивна та фасетна фільтрація, цілісність даних) покриті сценаріями `SCN-01` — `SCN-06`.
- **Готовність до кодингового циклу:** Стовпці для Task ID, Test ID та Code Unit визначені й будуть заповнюватися ШІ-кодинговим агентом на етапах TDD та імплементації під час наступних лабораторних робіт.
