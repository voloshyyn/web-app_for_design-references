# Матриця простежуваності вимог (Requirements Traceability Matrix, RTM)

- **Проєкт:** Система каталогізації та швидкого пошуку дизайн-референсів (`web-app_for_design-references`)
- **Етап SDLC:** Етап проєктування REST API специфікації (Лабораторна робота №4, після проходження API-GATE)
- **Призначення:** Забезпечення наскрізної двонаправленої простежуваності між вимогами SRS v1.0, критеріями прийняття (AC), BDD-сценаріями, SDD-тікетами беклогу, операціями REST API (OpenAPI 3.0.3), DTO-схемами, Mock-сценаріями та контрольними точками якості.

---

## 1. Матриця функціональних вимог (Functional Requirements Traceability)

| ID Вимоги | Короткий опис вимоги | Критерій прийняття (AC) | BDD-сценарій | SDD Тікети (Task IDs) | Модульний тест (Test ID) | Реалізація в коді (Code Unit) | Документація (Doc Ref) |
|---|---|---|---|---|---|---|---|
| **REQ-F-001** | Створення референсу із зовнішнього джерела (URL, назва, картинка) | `AC-F-001.1` (Успішне створення)<br>`AC-F-001.2` (Валідація обов'язкових полів) | `SCN-01`<br>`SCN-02` | `TEST-01`<br>`FEAT-01` | `tests/test_bdd_scenarios.py::test_create_reference_success`<br>`::test_create_reference_invalid_url` | `src/models.py::Reference` | `docs/user-guide.md#creating-reference` |
| **REQ-F-002** | Асоціація референсу з категорією (1:1) | `AC-F-002.1` (Прив'язка категорії)<br>`AC-F-002.2` (Дефолтна категорія "General") | `SCN-01`<br>`SCN-05` | `TEST-02`<br>`FEAT-02` | `tests/test_bdd_scenarios.py::test_category_assignment` | `src/models.py::Reference.category` | `docs/user-guide.md#categories` |
| **REQ-F-003** | Групування референсів у колекції (N:M) | `AC-F-003.1` (Додавання до багатьох колекцій) | `SCN-07` | `TEST-04`<br>`FEAT-04` | `tests/test_bdd_scenarios.py::test_collection_mapping` | `src/models.py::Collection` | `docs/user-guide.md#collections` |
| **REQ-F-004** | Управління тегами та фасетами | `AC-F-004.1` (Нормалізація тегів до нижнього регістру)<br>`AC-F-004.2` (Підтримка префіксів `namespace:val`) | `SCN-01`<br>`SCN-04` | `TEST-03`<br>`FEAT-03` | `tests/test_bdd_scenarios.py::test_tag_management_and_facets` | `src/models.py::Reference.add_tag` | `docs/user-guide.md#tagging` |
| **REQ-F-005** | Миттєва кон'юнктивна фільтрація за тегами (AND) | `AC-F-005.1` (Перетин множин тегів)<br>`AC-F-005.2` (Фільтрація за фасетами) | `SCN-03`<br>`SCN-04` | `TEST-03`<br>`FEAT-03` | `tests/test_bdd_scenarios.py::test_conjunctive_tag_filtering` | `src/models.py::Catalog.filter_by_tags` | `docs/user-guide.md#filtering` |
| **REQ-F-006** | Повнотекстовий пошук за назвою, нотатками та тегами | `AC-F-006.1` (Пошук без урахування регістру) | `SCN-06` | `TEST-04`<br>`FEAT-04` | `tests/test_bdd_scenarios.py::test_full_text_search` | `src/models.py::Catalog.search` | `docs/user-guide.md#search` |
| **REQ-F-007** | Перегляд детальної картки референсу з прев'ю | `AC-F-007.1` (Відображення всіх атрибутів та прев'ю) | — | `TEST-04`<br>`FEAT-04` | `tests/test_smoke.py::test_create_reference` | `src/models.py::Reference` | `docs/user-guide.md#reference-card` |
| **REQ-F-008** | Редагування та видалення референсу | `AC-F-008.1` (Оновлення метаданих)<br>`AC-F-008.2` (Видалення без залишкових зв'язків) | `SCN-05` | `TEST-04`<br>`FEAT-04` | `tests/test_bdd_scenarios.py::test_delete_reference` | `src/models.py::Catalog.remove_reference` | `docs/user-guide.md#managing-items` |

---

## 2. Матриця нефункціональних вимог (Non-Functional Requirements Traceability)

| ID Вимоги | Категорія вимоги | Критерій прийняття (AC) | BDD-сценарій | SDD Тікети (Task IDs) | Метод верифікації | Цільовий метричний показник |
|---|---|---|---|---|---|---|
| **REQ-NF-001** | Швидкодія (Performance) | `AC-NF-001.1` | `SCN-03` | `TEST-03`, `VERIF-ALL` | Автоматизований бенчмарк-тест часу виконання | Latency < 50 мс для каталогу з 1000 референсів |
| **REQ-NF-002** | Зручність використання (Usability) | `AC-NF-002.1` | `SCN-01` | `VALID-UX` | Аудит інтерфейсу (GOMS / KLM-аналіз дій людиною) | Додавання референсу з 3 тегами за ≤ 3 дії/кліки |
| **REQ-NF-003** | Надійність та цілісність (Reliability) | `AC-NF-003.1` | `SCN-05` | `TEST-02`, `FEAT-02`, `GATE-CORE` | Інтеграційні тести цілісності зв'язків моделей | 0% втрати даних при видаленні пов'язаних категорій (автопереведення в General) |
| **REQ-NF-004** | Безпека (Security) | `AC-NF-004.1` | `SCN-02` | `TEST-01`, `FEAT-01`, `GATE-CORE` | Тестування валідації вхідних даних (Fuzzing / Injection tests) | 100% блокування небезпечних протоколів (`javascript:`, `data:`) та екранування тексту |
| **REQ-NF-005** | Супровідність (Maintainability) | `AC-NF-005.1` | — | `VERIF-ALL`, `GATE-FINAL` | Статичний аналіз коду та аналіз покриття (Coverage) | 100% покриття бізнес-правил моделі модульними тестами, відповідність PEP 8 |

---

## 3. Матриця простежуваності REST API (OpenAPI Operations Traceability)

Ця секція встановлює прямий зв'язок між вимогами SRS v1.0 та формальним контрактом REST API (`spec/openapi.yaml`):

| ID Вимоги | HTTP Метод | URI Ресурсу | OpenAPI `operationId` | Схеми запиту / відповіді | Коди помилок (ProblemDetails) | Сценарій тестування Mock API |
|---|---|---|---|---|---|---|
| `REQ-F-001`<br>`REQ-NF-004` | `POST` | `/api/v1/references` | `createReference` | **Req:** `ReferenceCreateDto`<br>**Resp (201):** `ReferenceResponseDto` | `400` (VALIDATION_FAILED)<br>`422` (UNSAFE_URL_PROTOCOL) | `POS-01`<br>`NEG-01`<br>`NEG-02` |
| `REQ-F-002` | `GET`<br>`POST` | `/api/v1/categories`<br>`/api/v1/categories` | `listCategories`<br>`createCategory` | **Resp (200):** `CategoryResponseDto[]`<br>**Req:** `CategoryCreateDto` | `400` (CATEGORY_EXISTS)<br>`500` (INTERNAL_ERROR) | `POS-06` |
| `REQ-F-003` | `GET`<br>`POST`<br>`GET`<br>`DELETE`<br>`POST`<br>`DELETE` | `/api/v1/collections`<br>`/api/v1/collections`<br>`/api/v1/collections/{id}`<br>`/api/v1/collections/{id}`<br>`/api/v1/collections/{id}/references/{ref_id}`<br>`/api/v1/collections/{id}/references/{ref_id}` | `listCollections`<br>`createCollection`<br>`getCollectionById`<br>`deleteCollection`<br>`addReferenceToCollection`<br>`removeReferenceFromCollection` | **Req:** `CollectionCreateDto`<br>**Resp (200):** `CollectionWithReferencesDto`<br>**Resp (204):** No Content | `400` (VALIDATION_FAILED)<br>`404` (COLLECTION_NOT_FOUND)<br>`404` (REFERENCE_NOT_FOUND) | `POS-05`<br>`NEG-06` |
| `REQ-F-004`<br>`REQ-F-005` | `GET` | `/api/v1/references?tags=...` | `listReferences` | **Query:** `tags`, `category`<br>**Resp (200):** `ReferenceListResponse` | `400` (BAD_REQUEST)<br>`500` (INTERNAL_ERROR) | `POS-03` |
| `REQ-F-006` | `GET` | `/api/v1/references?q=...` | `listReferences` | **Query:** `q`<br>**Resp (200):** `ReferenceListResponse` | `400` (BAD_REQUEST)<br>`500` (INTERNAL_ERROR) | `POS-04` |
| `REQ-F-007` | `GET` | `/api/v1/references/{id}` | `getReferenceById` | **Resp (200):** `ReferenceResponseDto` | `404` (RESOURCE_NOT_FOUND)<br>`500` (INTERNAL_ERROR) | `POS-02`<br>`NEG-03` |
| `REQ-F-008` | `PUT`<br>`DELETE` | `/api/v1/references/{id}`<br>`/api/v1/references/{id}` | `updateReference`<br>`deleteReference` | **Req:** `ReferenceUpdateDto`<br>**Resp (200):** `ReferenceResponseDto`<br>**Resp (204):** No Content | `400` (VALIDATION_FAILED)<br>`404` (RESOURCE_NOT_FOUND)<br>`422` (UNSAFE_URL_PROTOCOL) | `POS-07` |
| `REQ-NF-001`<br>`REQ-NF-005` | `GET` | `/api/v1/health` | `getHealthStatus` | **Resp (200):** `HealthStatusDto` | `500` (INTERNAL_ERROR) | Сервісний SLA моніторинг |
| `REQ-NF-003` | `DELETE` | `/api/v1/categories/{name}` | `deleteCategory` | **Resp (200):** `CategoryMigrationReportDto` | `400` (PROTECTED_RESOURCE)<br>`404` (CATEGORY_NOT_FOUND) | `POS-08`<br>`NEG-04` |

---

## 4. Резюме простежуваності та статус готовності

- **Загальна кількість вимог SRS:** 13 (8 функціональних, 5 нефункціональних).
- **Кількість спроєктованих REST API операцій:** 15 операцій на 8 URI-шляхах.
- **Покриття вимог через REST API:** 100% функціональних та релевантних нефункціональних вимог мають відповідні HTTP-операції.
- **Покриття мок-тестами:** 14 автоматизованих сценаріїв (8 позитивних `POS-*`, 6 негативних `NEG-*`) покривають 100% критичних операцій та валідацій.
- **Єдина модель помилок:** 100% негативних статус-кодів (400, 404, 422, 500) типізовані через єдину схему `ProblemDetails` (RFC 7807).
- **Результат API-GATE:** **APPROVED (GO)** — дозвіл на перехід до фази TDD-імплементації в ЛР5.
