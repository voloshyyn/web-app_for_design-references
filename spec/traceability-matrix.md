# Матриця простежуваності — ЛР5

Дата: 2026-11-14. База SRS 1.0 + ADD-001, OpenAPI 1.1.0.
Ця актуальна матриця замінює старі посилання на неіснуючі назви тестів.
У таблиці наведено фактичні функції тестів. Автоматизація не замінює UX-валідацію.

| Вимога / AC / сценарій | Тести | Код / стан |
|---|---|---|
| REQ-F-001; AC-F-001.1..3; SCN-01/02 | test_api.py::test_reference_lifecycle, test_input_rejection, test_malformed_json_and_atomic_update | service.validate_reference, createReference; PASS |
| REQ-F-002; AC-F-002.1/2; SCN-01/05 | test_api.py::test_categories, test_reference_lifecycle | createCategory, deleteCategory, createReference; PASS |
| REQ-F-003; AC-F-003.1/2; SCN-07 | test_api.py::test_collections | collection operations; PASS |
| REQ-F-004; AC-F-004.1/2; SCN-01/04 | test_api.py::test_reference_lifecycle, test_search_filter_and_pagination; test_verification.py::test_model_rules | Reference tags/facets; PASS |
| REQ-F-005; AC-F-005.1/2; SCN-03/04 | test_api.py::test_search_filter_and_pagination, test_bad_pagination | Catalog.filter_by_tags, listReferences; PASS |
| REQ-F-006; AC-F-006.1/2; SCN-06 | test_api.py::test_search_filter_and_pagination; test_verification.py::test_model_rules | Catalog.search; PASS |
| REQ-F-007; AC-F-007.1 | test_api.py::test_reference_lifecycle | getReferenceById повертає всі дані; API PASS, візуальна картка/UI PENDING |
| REQ-F-008; AC-F-008.1/2; SCN-05/07 | test_api.py::test_reference_lifecycle, test_malformed_json_and_atomic_update, test_collections | updateReference, deleteReference; PASS |
| REQ-F-009; AC-F-009.1..5; SCN-08 | test_addendum.py::test_rename_preserves_identity_links_and_persistence, test_rename_invalid_is_atomic, test_rename_missing_and_max_length | updateCollection; PASS |
| REQ-NF-001; AC-NF-001.1 | test_verification.py::test_sla_1000_references | 1000 записів, 3 теги, 20 повторень; domain SLA PASS, не UI latency |
| REQ-NF-002; AC-NF-002.1 | docs/lab5-human-validation.md | PENDING: немає UI для оцінки 3 кліків |
| REQ-NF-003; AC-NF-003.1; SCN-05 | test_api.py::test_categories; test_verification.py::test_save_failure_rollback_and_error_log, test_restart_preserves_collections_categories | category fallback + atomic repository; PASS |
| REQ-NF-004; AC-NF-004.1; SCN-02 | test_api.py::test_input_rejection, test_malformed_json_and_atomic_update | validate_reference, JSON HTML escaping; API перевірено, рендеринг клієнта потребує textContent |
| REQ-NF-005; AC-NF-005.1 | tests/test_bdd_scenarios.py, test_verification.py::test_model_rules; scripts/check_lab5.py | 98.04% line coverage models >=95%; PASS |
| SRS 3.1 локальне збереження | test_api.py::test_health_persistence_and_audit; test_verification.py::test_corrupt_store_fails_without_overwrite | repository.py; PASS, експорт/імпорт через JSON-файл |
| ЛР5 обов'язкові LOGS | test_api.py::test_health_persistence_and_audit; test_verification.py::test_save_failure_rollback_and_error_log; test_addendum.py::test_rename_preserves_identity_links_and_persistence | audit.py; PASS |
| Контракт 15 + 1 операцій | усі HTTP calls у test_api.py/test_addendum.py перевіряють response schema; test_verification.py::test_openapi_valid_and_backwards_compatible | api.py + OpenAPI; PASS |

Назви файлів тестів у таблиці відносні до tests/; назви компонентів — до src/.
Початкові SCN-01..07 також залишаються в tests/test_bdd_scenarios.py під фактичними
іменами test_scn_01_create_valid_reference .. test_scn_07_collection_management.

Артефакти: docs/lab5-plan.md, spec/addendum-001-collection-rename.md,
logs/lab5-test-gate.md, logs/lab5-addendum-test-gate.md, logs/lab5-final-gate.md.
Тікети LAB5-01..06 локальні. Людська валідація та формальний Gate — PENDING/REVISE.

## Актуалізація після аудиту 15.11.2026
- Поточні TEST-GATE / SPEC-ADDENDUM-GATE: технічно прийнято агентом за
  прямим дорученням користувача; див. logs/lab5-final-gate.md.
- tests/test_audit_fixes.py перевіряє malformed path + audit, версію health,
  обчислення статусів і генерацію PDF зі статусом FAIL.
- REQ-F-001..009: logs/lab5-fault-detection.json — 9 перевірок вимкнення
  операцій; це новий контроль чутливості, не історичний TDD.
- Делегована валідація: logs/lab5-agent-validation.json, 14 HTTP-дій із
  повним перезапуском сервера. Людська валідація NOT_PERFORMED.
- Тікет ADD-001: docs/tickets/LAB5-04.md. UI-критерії залишаються поза
  серверним обсягом; повна формальна відповідність людському пункту PDF
  та історична повнота TDD не заявляються.
