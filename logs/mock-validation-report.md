# Звіт про автоматичну верифікацію Mock API за специфікацією OpenAPI

- **Проєкт:** Система каталогізації та швидкого пошуку дизайн-референсів (`web-app_for_design-references`)
- **Етап SDLC:** Етап проєктування REST API контракту (Лабораторна робота №4)
- **Дата верифікації:** 31 жовтня 2026 р.
- **Статус тестування:** **PASSED (100% контрактна відповідність)**
- **Результати:** 14/14 сценаріїв пройдено (100.0%)
  - Позитивні сценарії: 8/8 успішно
  - Негативні сценарії: 6/6 успішно
- **Середня затримка відповіді Mock API:** 2.57 мс (Цільовий показник SLA < 50 мс)

---

## 1. Зведена таблиця виконання позитивних і негативних сценаріїв

| ID | Тип | Назва сценарію | REQ-ID | Метод & Endpoint | Очікуваний HTTP | Отриманий HTTP | Latency (мс) | Статус |
|---|---|---|---|---|---|---|---|---|
| **POS-01** | Positive | Create visual reference with valid fields (REQ-F-001) | `REQ-F-001` | `POST /references` | `201` | `201` | 29.7 | **PASSED** |
| **POS-02** | Positive | Get reference detailed card by ID (REQ-F-007) | `REQ-F-007` | `GET /references/ref-001` | `200` | `200` | 0.6 | **PASSED** |
| **POS-03** | Positive | Conjunctive tag filtering (AND semantics) (REQ-F-005) | `REQ-F-005` | `GET /references?tags=minimalism,landing` | `200` | `200` | 0.5 | **PASSED** |
| **POS-04** | Positive | Full-text case-insensitive search (REQ-F-006) | `REQ-F-006` | `GET /references?q=dashboard` | `200` | `200` | 0.4 | **PASSED** |
| **POS-05** | Positive | Add reference to collection board (N:M relation) (REQ-F-003) | `REQ-F-003` | `POST /collections/col-01/references/ref-002` | `200` | `200` | 0.6 | **PASSED** |
| **POS-06** | Positive | List registered categories with default 'General' (REQ-F-002) | `REQ-F-002` | `GET /categories` | `200` | `200` | 0.5 | **PASSED** |
| **POS-07** | Positive | Update reference metadata (REQ-F-008) | `REQ-F-008` | `PUT /references/ref-001` | `200` | `200` | 0.5 | **PASSED** |
| **POS-08** | Positive | Zero-loss category delete with Fallback to 'General' (REQ-NF-003) | `REQ-NF-003` | `DELETE /categories/Branding` | `200` | `200` | 0.5 | **PASSED** |
| **NEG-01** | Negative | Security: Reject unsafe javascript: protocol (REQ-NF-004) | `REQ-NF-004` | `POST /references` | `422` | `422` | 0.5 | **PASSED** |
| **NEG-02** | Negative | Validation: Reject reference with empty title (REQ-F-001) | `REQ-F-001` | `POST /references` | `400` | `400` | 0.5 | **PASSED** |
| **NEG-03** | Negative | Resource Not Found: Query non-existent reference ID (REQ-F-007) | `REQ-F-007` | `GET /references/non-existent-ref-999` | `404` | `404` | 0.4 | **PASSED** |
| **NEG-04** | Negative | Integrity: Reject deletion of protected 'General' category (REQ-NF-003) | `REQ-NF-003` | `DELETE /categories/General` | `400` | `400` | 0.4 | **PASSED** |
| **NEG-05** | Negative | Malformed Request: Reject malformed JSON body (REQ-NF-005) | `REQ-NF-005` | `POST /references` | `400` | `400` | 0.5 | **PASSED** |
| **NEG-06** | Negative | Not Found: Add reference to non-existent collection (REQ-F-003) | `REQ-F-003` | `POST /collections/non-existent-col-999/references/ref-001` | `404` | `404` | 0.4 | **PASSED** |

---

## 2. Аналіз відповідності єдиній моделі помилок (RFC 7807)

Усі негативні сценарії (`NEG-01` — `NEG-06`) повернули структуровану відповідь типу `application/problem+json`, що містить обов'язкові атрибути єдиної моделі помилок:
- `type`: URI-дескриптор помилки
- `title`: Людинозрозумілий заголовок
- `status`: Числовий HTTP-код стану
- `code`: Машинозчитуваний внутрішній код помилки (`UNSAFE_URL_PROTOCOL`, `VALIDATION_FAILED`, `RESOURCE_NOT_FOUND`, `PROTECTED_RESOURCE`, `MALFORMED_JSON`)
- `detail`: Деталізований опис причини виникнення інциденту
- `instance`: Відносний URI запиту
- `invalid_params`: Масив некоректних полів із причинами відхилення (у сценаріях 400/422).

---

## 3. Висновок для контрольної точки API-GATE

Mock API успішно запустився без створення серверного виробничого коду, що підтверджує можливість повноцінної паралельної розробки клієнтської частини до початку TDD-імплементації в ЛР5. Усі 100% сценаріїв (14/14) відтворюють контракт специфікації `spec/openapi.yaml` без девіацій.