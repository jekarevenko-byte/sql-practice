# SQL для QA: запросы и проверка данных на базе Chinook

[![SQL Tests](https://github.com/jekarevenko-byte/qa-sql-practice/actions/workflows/tests.yml/badge.svg)](https://github.com/jekarevenko-byte/qa-sql-practice/actions/workflows/tests.yml)
![SQLite](https://img.shields.io/badge/SQLite-3.25%2B-003B57?logo=sqlite&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-8.3-green)

Учебный проект: 42 SQL-запроса по нарастающей сложности и автотесты, которые проверяют сами запросы и качество данных. База — [Chinook](https://github.com/lerocha/chinook-database) (музыкальный магазин: клиенты, счета, треки, плейлисты), SQLite, лежит в репозитории, ставить ничего не нужно.

## Что здесь показано

| Навык | Где смотреть |
|---|---|
| SELECT, фильтры, NULL, LIKE, диапазоны дат | `sql/01_select_basics.sql` |
| INNER/LEFT JOIN, анти-джойн, самосоединение | `sql/02_joins.sql` |
| GROUP BY, HAVING, агрегаты, `strftime` | `sql/03_group_by.sql` |
| Подзапросы, EXISTS/IN, CTE | `sql/04_subqueries.sql` |
| Оконные функции: RANK, ROW_NUMBER, LAG, накопительный итог | `sql/05_window_functions.sql` |
| QA-проверки данных: целостность, дубли, формат, бизнес-правила | `sql/06_data_validation.sql` |
| Перекрёстная проверка результата SQL расчётом на Python | `tests/test_queries.py` |
| Проверка, что проверки умеют находить дефекты | `tests/test_data_quality.py` |
| Сверка ответа API с данными в БД | `tests/test_api_db_consistency.py`, `src/compare.py` |

## Структура

```
qa-sql-practice/
├── data/chinook.sqlite          ← база (лицензия: data/CHINOOK_LICENSE.md)
├── sql/                         ← запросы, у каждого метка "-- name: ..."
├── src/
│   ├── sql_loader.py            ← читает запросы по именам, подключение read-only
│   └── compare.py               ← сравнение JSON ответа API со строкой БД
├── tests/
│   ├── test_queries.py          ← результат запроса == независимый расчёт
│   ├── test_data_quality.py     ← проверки на чистой базе и на испорченной копии
│   ├── test_api_db_consistency.py
│   └── fixtures/                ← пример ответа API
└── .github/workflows/tests.yml  ← CI
```

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
allure serve allure-results     # по желанию, нужен Allure CLI
```

Запросы можно выполнять и без Python: откройте `data/chinook.sqlite` в [DB Browser for SQLite](https://sqlitebrowser.org/) и копируйте запросы из `sql/`.

## Как устроены проверки

**1. Перекрёстная проверка (cross-check).** Результат запроса сравнивается не с «магическим числом», а с независимым расчётом: сумма по странам считается в Python по сырым счетам, `LEFT JOIN … IS NULL` сверяется с `NOT IN`, число строк после JOIN должно совпасть с числом треков.

**2. Проверка самих проверок.** Каждая проверка качества данных возвращает *нарушения*. На чистой базе их 0, а затем в копии базы в памяти создаётся дефект (испорчена сумма счёта, удалён трек, дубликат email, отрицательная цена…), и проверка обязана его найти. Проверка, которая не умеет падать, бесполезна.

**3. Данные после API.** `assert_api_matches_db` сверяет поля ответа API с колонками БД и показывает все расхождения сразу, с допуском на погрешность float. В реальном проекте ответ берётся из клиента проекта [qa_api_tests](https://github.com/jekarevenko-byte/qa_api_tests).

## Примечания по данным

- Даты счетов в этой версии Chinook: 2021-01-01 … 2025-12-22.
- Внешние ключи в SQLite по умолчанию не проверяются, поэтому проверки ссылочной целостности написаны запросами.
- Тесты открывают базу в режиме read-only, а «ломают» только копию в памяти.
