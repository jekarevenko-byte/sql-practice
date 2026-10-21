-- Уровень 4. Подзапросы, EXISTS, IN, CTE.

-- name: tracks_longer_than_average
-- Скалярный подзапрос
SELECT TrackId, Name, Milliseconds
FROM Track
WHERE Milliseconds > (SELECT AVG(Milliseconds) FROM Track)
ORDER BY TrackId;

-- name: customers_above_average_spend
-- Подзапрос в FROM: сначала сумма по клиенту, потом сравнение со средним по клиентам
SELECT s.CustomerId, s.TotalSpent
FROM (SELECT CustomerId, ROUND(SUM(Total), 2) AS TotalSpent
      FROM Invoice
      GROUP BY CustomerId) AS s
WHERE s.TotalSpent > (SELECT AVG(x.TotalSpent)
                      FROM (SELECT SUM(Total) AS TotalSpent
                            FROM Invoice
                            GROUP BY CustomerId) AS x)
ORDER BY s.TotalSpent DESC, s.CustomerId;

-- name: albums_with_more_than_20_tracks
-- IN с подзапросом
SELECT AlbumId, Title
FROM Album
WHERE AlbumId IN (SELECT AlbumId
                  FROM Track
                  GROUP BY AlbumId
                  HAVING COUNT(*) > 20)
ORDER BY AlbumId;

-- name: tracks_never_sold
-- NOT EXISTS безопаснее NOT IN: NOT IN ломается, если в подзапросе есть NULL
SELECT t.TrackId, t.Name
FROM Track t
WHERE NOT EXISTS (SELECT 1 FROM InvoiceLine il WHERE il.TrackId = t.TrackId)
ORDER BY t.TrackId;

-- name: customers_without_invoices
SELECT c.CustomerId, c.FirstName, c.LastName
FROM Customer c
WHERE NOT EXISTS (SELECT 1 FROM Invoice i WHERE i.CustomerId = c.CustomerId)
ORDER BY c.CustomerId;

-- name: best_selling_genre_cte
-- CTE (WITH) делает запрос читаемым: продажи по жанрам, берём лидера
WITH genre_sales AS (
    SELECT g.Name AS Genre, SUM(il.Quantity) AS UnitsSold
    FROM InvoiceLine il
    JOIN Track t ON t.TrackId = il.TrackId
    JOIN Genre g ON g.GenreId = t.GenreId
    GROUP BY g.GenreId
)
SELECT Genre, UnitsSold
FROM genre_sales
ORDER BY UnitsSold DESC, Genre
LIMIT 1;
