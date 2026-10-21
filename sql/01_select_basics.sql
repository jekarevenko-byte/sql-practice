-- Уровень 1. Базовые SELECT: фильтры, сортировка, NULL, LIKE, диапазоны дат.
-- Формат: каждый запрос начинается с комментария "-- name: <имя>", по нему тесты находят запрос.

-- name: customers_from_brazil
-- Клиенты из Бразилии: конкатенация строк, фильтр, сортировка
SELECT CustomerId,
       FirstName || ' ' || LastName AS FullName,
       City
FROM Customer
WHERE Country = 'Brazil'
ORDER BY CustomerId;

-- name: customers_without_company
-- Работа с NULL: сравнение через IS NULL, а не "= NULL"
SELECT CustomerId, FirstName, LastName
FROM Customer
WHERE Company IS NULL
ORDER BY CustomerId;

-- name: tracks_longer_than_10_minutes
-- Фильтр по числовому полю, 600000 мс = 10 минут
SELECT TrackId, Name, Milliseconds
FROM Track
WHERE Milliseconds > 600000
ORDER BY Milliseconds DESC, TrackId;

-- name: albums_with_greatest_in_title
-- LIKE: подстрока без учёта регистра (в SQLite LIKE регистронезависим для ASCII)
SELECT AlbumId, Title
FROM Album
WHERE Title LIKE '%greatest%'
ORDER BY AlbumId;

-- name: invoices_first_quarter_2023
-- Диапазон дат: границу "до" лучше делать строгой (< 1 апреля), а не BETWEEN по последней секунде
SELECT InvoiceId, InvoiceDate, Total
FROM Invoice
WHERE InvoiceDate >= '2023-01-01'
  AND InvoiceDate <  '2023-04-01'
ORDER BY InvoiceDate, InvoiceId;

-- name: distinct_billing_countries
-- DISTINCT: уникальные значения
SELECT DISTINCT BillingCountry
FROM Invoice
ORDER BY BillingCountry;
