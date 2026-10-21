-- Уровень 3. Агрегаты: GROUP BY, HAVING, функции дат.

-- name: revenue_by_country
-- Выручка по странам; ROUND нужен из-за погрешностей чисел с плавающей точкой
SELECT BillingCountry AS Country,
       COUNT(*)               AS Invoices,
       ROUND(SUM(Total), 2)   AS Revenue
FROM Invoice
GROUP BY BillingCountry
ORDER BY Revenue DESC, Country;

-- name: top10_customers_by_spend
SELECT c.CustomerId,
       c.FirstName || ' ' || c.LastName AS Customer,
       ROUND(SUM(i.Total), 2)           AS TotalSpent
FROM Customer c
JOIN Invoice i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId
ORDER BY TotalSpent DESC, c.CustomerId
LIMIT 10;

-- name: tracks_per_genre
-- LEFT JOIN, чтобы жанры без треков тоже попали в результат с нулём
SELECT g.GenreId, g.Name AS Genre, COUNT(t.TrackId) AS Tracks
FROM Genre g
LEFT JOIN Track t ON t.GenreId = g.GenreId
GROUP BY g.GenreId
ORDER BY Tracks DESC, g.GenreId;

-- name: monthly_revenue
-- strftime группирует даты по месяцам
SELECT strftime('%Y-%m', InvoiceDate) AS Month,
       ROUND(SUM(Total), 2)           AS Revenue
FROM Invoice
GROUP BY Month
ORDER BY Month;

-- name: countries_with_more_than_4_customers
-- HAVING фильтрует уже после агрегации (WHERE так сделать не может)
SELECT Country, COUNT(*) AS Customers
FROM Customer
GROUP BY Country
HAVING COUNT(*) > 4
ORDER BY Customers DESC, Country;

-- name: average_track_length_per_album
SELECT al.AlbumId,
       al.Title,
       COUNT(t.TrackId)                     AS Tracks,
       ROUND(AVG(t.Milliseconds) / 60000.0, 2) AS AvgMinutes
FROM Album al
JOIN Track t ON t.AlbumId = al.AlbumId
GROUP BY al.AlbumId
ORDER BY al.AlbumId;
