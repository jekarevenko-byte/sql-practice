-- Уровень 2. JOIN: INNER, LEFT, самосоединение, несколько таблиц.

-- name: tracks_with_album_artist_genre
-- INNER JOIN по цепочке Track -> Album -> Artist; LEFT JOIN к Genre, чтобы не потерять треки без жанра
SELECT t.TrackId,
       t.Name   AS Track,
       al.Title AS Album,
       ar.Name  AS Artist,
       g.Name   AS Genre
FROM Track t
JOIN Album  al ON al.AlbumId  = t.AlbumId
JOIN Artist ar ON ar.ArtistId = al.ArtistId
LEFT JOIN Genre g ON g.GenreId = t.GenreId
ORDER BY t.TrackId;

-- name: artists_without_albums
-- Анти-джойн: LEFT JOIN + IS NULL находит артистов без альбомов
SELECT ar.ArtistId, ar.Name
FROM Artist ar
LEFT JOIN Album al ON al.ArtistId = ar.ArtistId
WHERE al.AlbumId IS NULL
ORDER BY ar.ArtistId;

-- name: customers_with_support_rep
-- Клиент и его сотрудник поддержки
SELECT c.CustomerId,
       c.FirstName || ' ' || c.LastName AS Customer,
       e.FirstName || ' ' || e.LastName AS SupportRep
FROM Customer c
JOIN Employee e ON e.EmployeeId = c.SupportRepId
ORDER BY c.CustomerId;

-- name: employees_with_manager
-- Самосоединение: сотрудник и его руководитель (у главы компании руководителя нет, поэтому LEFT JOIN)
SELECT e.EmployeeId,
       e.FirstName || ' ' || e.LastName AS Employee,
       m.FirstName || ' ' || m.LastName AS Manager
FROM Employee e
LEFT JOIN Employee m ON m.EmployeeId = e.ReportsTo
ORDER BY e.EmployeeId;

-- name: invoice_lines_detailed
-- Полная детализация счёта: клиент, трек, сумма строки
SELECT i.InvoiceId,
       c.LastName      AS Customer,
       t.Name          AS Track,
       il.UnitPrice,
       il.Quantity,
       il.UnitPrice * il.Quantity AS LineTotal
FROM InvoiceLine il
JOIN Invoice  i ON i.InvoiceId  = il.InvoiceId
JOIN Customer c ON c.CustomerId = i.CustomerId
JOIN Track    t ON t.TrackId    = il.TrackId
ORDER BY il.InvoiceLineId;
