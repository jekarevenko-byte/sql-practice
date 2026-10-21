-- Уровень 6. QA-проверки качества данных.
-- Каждый запрос возвращает НАРУШЕНИЯ. Пустой результат = проверка пройдена.

-- name: invoice_total_differs_from_lines
-- Сумма счёта должна равняться сумме его строк (допуск на копейки из-за float)
SELECT i.InvoiceId, i.Total AS InvoiceTotal, ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS LinesTotal
FROM Invoice i
JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
GROUP BY i.InvoiceId
HAVING ABS(i.Total - SUM(il.UnitPrice * il.Quantity)) > 0.005;

-- name: invoices_without_lines
SELECT i.InvoiceId
FROM Invoice i
WHERE NOT EXISTS (SELECT 1 FROM InvoiceLine il WHERE il.InvoiceId = i.InvoiceId);

-- name: orphan_invoice_lines
-- Строки, ссылающиеся на несуществующие счета или треки (нарушение ссылочной целостности)
SELECT il.InvoiceLineId
FROM InvoiceLine il
WHERE NOT EXISTS (SELECT 1 FROM Invoice i WHERE i.InvoiceId = il.InvoiceId)
   OR NOT EXISTS (SELECT 1 FROM Track   t WHERE t.TrackId   = il.TrackId);

-- name: orphan_invoices
SELECT i.InvoiceId
FROM Invoice i
WHERE NOT EXISTS (SELECT 1 FROM Customer c WHERE c.CustomerId = i.CustomerId);

-- name: orphan_tracks
-- У трека есть альбом / тип медиа, на которые нет записи
SELECT t.TrackId
FROM Track t
WHERE (t.AlbumId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM Album a WHERE a.AlbumId = t.AlbumId))
   OR NOT EXISTS (SELECT 1 FROM MediaType m WHERE m.MediaTypeId = t.MediaTypeId);

-- name: tracks_without_album
-- Не ошибка схемы, но кандидат на вопрос к аналитику/разработчику
SELECT TrackId, Name
FROM Track
WHERE AlbumId IS NULL;

-- name: tracks_without_genre
SELECT TrackId, Name
FROM Track
WHERE GenreId IS NULL;

-- name: duplicate_customer_emails
SELECT Email, COUNT(*) AS Cnt
FROM Customer
GROUP BY LOWER(Email)
HAVING COUNT(*) > 1;

-- name: customers_with_invalid_email
-- Грубая проверка формата: должен быть символ @ и точка после него
SELECT CustomerId, Email
FROM Customer
WHERE Email IS NULL
   OR Email NOT LIKE '%_@_%._%';

-- name: non_positive_values
-- Цена, количество, длительность и размер должны быть строго больше нуля
SELECT 'Track' AS Tbl, TrackId AS Id
FROM Track
WHERE UnitPrice <= 0 OR Milliseconds <= 0 OR (Bytes IS NOT NULL AND Bytes <= 0)
UNION ALL
SELECT 'InvoiceLine', InvoiceLineId
FROM InvoiceLine
WHERE UnitPrice <= 0 OR Quantity <= 0;

-- name: employees_with_missing_manager
SELECT e.EmployeeId
FROM Employee e
WHERE e.ReportsTo IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM Employee m WHERE m.EmployeeId = e.ReportsTo);

-- name: customers_with_missing_support_rep
SELECT c.CustomerId
FROM Customer c
WHERE c.SupportRepId IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM Employee e WHERE e.EmployeeId = c.SupportRepId);

-- name: playlist_track_orphans
SELECT pt.PlaylistId, pt.TrackId
FROM PlaylistTrack pt
WHERE NOT EXISTS (SELECT 1 FROM Playlist p WHERE p.PlaylistId = pt.PlaylistId)
   OR NOT EXISTS (SELECT 1 FROM Track    t WHERE t.TrackId    = pt.TrackId);

-- name: duplicate_artist_names
SELECT Name, COUNT(*) AS Cnt
FROM Artist
GROUP BY Name
HAVING COUNT(*) > 1;

-- name: invoices_dated_in_future
SELECT InvoiceId, InvoiceDate
FROM Invoice
WHERE InvoiceDate > datetime('now');
