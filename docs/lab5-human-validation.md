# Людська валідація — статус PENDING

Автотест підтверджує відповідність формалізованій вимозі (верифікація).
Лише людина оцінює, чи вирішує реалізація її потребу (валідація).

1. Виконати `.\lab5.ps1 demo`, прочитати відповіді створення, фільтрації,
   прив'язки до дошки й перейменування. Перевірити, що це відповідає задуму.
2. Виконати `.\lab5.ps1 serve`. В іншому PowerShell:

```powershell
$base = 'http://127.0.0.1:8000/api/v1'
$ref = Invoke-RestMethod "$base/references" -Method Post -ContentType 'application/json' -Body '{"title":"My reference","url":"https://example.org","tags":["mobile","dark"]}'
$board = Invoke-RestMethod "$base/collections" -Method Post -ContentType 'application/json' -Body '{"name":"Moodboard"}'
Invoke-RestMethod "$base/collections/$($board.id)/references/$($ref.id)" -Method Post
Invoke-RestMethod "$base/collections/$($board.id)" -Method Put -ContentType 'application/json' -Body '{"name":"Client pitch"}'
Invoke-RestMethod "$base/references?tags=mobile,dark"
```

3. Перевірити, що назва дошки змінилася, а ID референсу залишився.
   Зупинити й повторно запустити сервер, переконатися, що дані збережено.
4. Оцінити користь перейменування для своєї роботи. Занотувати фактичний
   результат і зауваження нижче, не підміняти їх результатами автотестів.
5. Переглянути TEST-GATE та SPEC-ADDENDUM-GATE, записати власне рішення.
   UX «до 3 кліків» стосується майбутнього інтерфейсу, за API його не приймати.

Перевірив(ла): __________  Дата: __________
Спостереження: __________  Рішення: GO / REVISE / STOP __________

Після перевірки доповнити logs/lab5-final-gate.md і сформувати актуальний
протокол. Не позначати всі SRS-вимоги виконаними, доки UX не перевірено.
