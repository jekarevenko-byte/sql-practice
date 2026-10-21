-- Уровень 5. Оконные функции (SQLite 3.25+).

-- name: customer_rank_within_country
-- RANK() внутри страны: одинаковые суммы получают одинаковый ранг
SELECT Country, CustomerId, TotalSpent,
       RANK() OVER (PARTITION BY Country ORDER BY TotalSpent DESC) AS CountryRank
FROM (SELECT c.Country, c.CustomerId, ROUND(SUM(i.Total), 2) AS TotalSpent
      FROM Customer c
      JOIN Invoice i ON i.CustomerId = c.CustomerId
      GROUP BY c.CustomerId)
ORDER BY Country, CountryRank, CustomerId;

-- name: running_revenue_by_month
-- Накопительный итог: сумма окна от начала до текущей строки
SELECT Month,
       Revenue,
       ROUND(SUM(Revenue) OVER (ORDER BY Month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS RunningRevenue
FROM (SELECT strftime('%Y-%m', InvoiceDate) AS Month, ROUND(SUM(Total), 2) AS Revenue
      FROM Invoice
      GROUP BY Month)
ORDER BY Month;

-- name: month_over_month_change
-- LAG: значение предыдущей строки, для первого месяца NULL
SELECT Month,
       Revenue,
       LAG(Revenue) OVER (ORDER BY Month)                    AS PrevRevenue,
       ROUND(Revenue - LAG(Revenue) OVER (ORDER BY Month), 2) AS Change
FROM (SELECT strftime('%Y-%m', InvoiceDate) AS Month, ROUND(SUM(Total), 2) AS Revenue
      FROM Invoice
      GROUP BY Month)
ORDER BY Month;

-- name: top_selling_track_per_genre
-- ROW_NUMBER для выбора "лучшего в группе"; тай-брейк по TrackId делает результат детерминированным
SELECT Genre, Track, UnitsSold
FROM (SELECT g.Name AS Genre,
             t.Name AS Track,
             SUM(il.Quantity) AS UnitsSold,
             ROW_NUMBER() OVER (PARTITION BY g.GenreId
                                ORDER BY SUM(il.Quantity) DESC, t.TrackId) AS rn
      FROM InvoiceLine il
      JOIN Track t ON t.TrackId = il.TrackId
      JOIN Genre g ON g.GenreId = t.GenreId
      GROUP BY g.GenreId, t.TrackId)
WHERE rn = 1
ORDER BY Genre;
