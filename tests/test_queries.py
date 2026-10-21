"""
Cross-check technique: the result of each SQL query is compared with an independent
calculation done in Python over the raw table rows (or with an alternative SQL formulation).
"""

from collections import defaultdict

import pytest

from src.sql_loader import QUERIES, run


def rows(db, sql):
    return db.execute(sql).fetchall()


# ── meta ──────────────────────────────────────────────────────────────────────

def test_all_queries_loaded_and_unique():
    assert len(QUERIES) >= 40


@pytest.mark.parametrize("name", sorted(QUERIES))
def test_every_query_executes(db, name):
    run(db, name)  # must not raise


# ── 01 basics ─────────────────────────────────────────────────────────────────

def test_customers_from_brazil_matches_python_filter(db):
    expected = sorted(r["CustomerId"] for r in rows(db, "SELECT * FROM Customer") if r["Country"] == "Brazil")
    actual = [r["CustomerId"] for r in run(db, "customers_from_brazil")]
    assert actual == expected and len(actual) > 0


def test_null_company_uses_is_null_not_equals(db):
    wrong = rows(db, "SELECT CustomerId FROM Customer WHERE Company = NULL")
    assert wrong == [], "'= NULL' never matches - this is the classic bug the IS NULL query avoids"
    right = run(db, "customers_without_company")
    with_company = rows(db, "SELECT COUNT(*) AS n FROM Customer WHERE Company IS NOT NULL")[0]["n"]
    assert len(right) + with_company == rows(db, "SELECT COUNT(*) AS n FROM Customer")[0]["n"]


def test_long_tracks_are_really_longer_than_ten_minutes(db):
    result = run(db, "tracks_longer_than_10_minutes")
    assert result and all(r["Milliseconds"] > 600_000 for r in result)
    total = rows(db, "SELECT COUNT(*) AS n FROM Track WHERE Milliseconds > 600000")[0]["n"]
    assert len(result) == total


def test_like_is_case_insensitive(db):
    upper = rows(db, "SELECT AlbumId FROM Album WHERE Title LIKE '%GREATEST%'")
    assert [r["AlbumId"] for r in upper] == [r["AlbumId"] for r in run(db, "albums_with_greatest_in_title")]


def test_q1_2023_invoices_are_inside_the_quarter(db):
    result = run(db, "invoices_first_quarter_2023")
    assert result
    assert all("2023-01-01" <= r["InvoiceDate"] < "2023-04-01" for r in result)


def test_distinct_countries_have_no_duplicates(db):
    countries = [r["BillingCountry"] for r in run(db, "distinct_billing_countries")]
    assert len(countries) == len(set(countries))


# ── 02 joins ──────────────────────────────────────────────────────────────────

def test_track_join_does_not_lose_or_duplicate_rows(db):
    assert len(run(db, "tracks_with_album_artist_genre")) == rows(db, "SELECT COUNT(*) AS n FROM Track")[0]["n"]


def test_artists_without_albums_equals_alternative_formulation(db):
    alt = rows(db, "SELECT ArtistId FROM Artist WHERE ArtistId NOT IN (SELECT ArtistId FROM Album) ORDER BY ArtistId")
    assert [r["ArtistId"] for r in run(db, "artists_without_albums")] == [r["ArtistId"] for r in alt]


def test_every_customer_has_a_support_rep_row(db):
    assert len(run(db, "customers_with_support_rep")) == rows(db, "SELECT COUNT(*) AS n FROM Customer")[0]["n"]


def test_exactly_one_employee_has_no_manager(db):
    result = run(db, "employees_with_manager")
    assert len(result) == rows(db, "SELECT COUNT(*) AS n FROM Employee")[0]["n"]
    assert sum(1 for r in result if r["Manager"] is None) == 1


def test_invoice_lines_detailed_line_totals(db):
    result = run(db, "invoice_lines_detailed")
    assert len(result) == rows(db, "SELECT COUNT(*) AS n FROM InvoiceLine")[0]["n"]
    assert all(r["LineTotal"] == pytest.approx(r["UnitPrice"] * r["Quantity"]) for r in result)


# ── 03 group by ───────────────────────────────────────────────────────────────

def test_revenue_by_country_matches_python_aggregation(db):
    expected = defaultdict(float)
    for r in rows(db, "SELECT BillingCountry, Total FROM Invoice"):
        expected[r["BillingCountry"]] += r["Total"]
    actual = {r["Country"]: r["Revenue"] for r in run(db, "revenue_by_country")}
    assert actual.keys() == expected.keys()
    assert all(actual[k] == pytest.approx(expected[k], abs=0.01) for k in expected)


def test_revenue_by_country_is_sorted_descending(db):
    revenue = [r["Revenue"] for r in run(db, "revenue_by_country")]
    assert revenue == sorted(revenue, reverse=True)


def test_top10_customers(db):
    result = run(db, "top10_customers_by_spend")
    assert len(result) == 10
    spent = [r["TotalSpent"] for r in result]
    assert spent == sorted(spent, reverse=True)
    best_python = max(
        sum(i["Total"] for i in rows(db, f"SELECT Total FROM Invoice WHERE CustomerId = {c['CustomerId']}"))
        for c in rows(db, "SELECT CustomerId FROM Customer")
    )
    assert spent[0] == pytest.approx(best_python, abs=0.01)


def test_tracks_per_genre_adds_up_to_all_tracks(db):
    result = run(db, "tracks_per_genre")
    assert sum(r["Tracks"] for r in result) == rows(db, "SELECT COUNT(*) AS n FROM Track WHERE GenreId IS NOT NULL")[0]["n"]
    assert len(result) == rows(db, "SELECT COUNT(*) AS n FROM Genre")[0]["n"]  # LEFT JOIN keeps empty genres


def test_monthly_revenue_sums_to_total(db):
    total = rows(db, "SELECT SUM(Total) AS s FROM Invoice")[0]["s"]
    assert sum(r["Revenue"] for r in run(db, "monthly_revenue")) == pytest.approx(total, abs=0.05)


def test_countries_with_more_than_4_customers(db):
    result = run(db, "countries_with_more_than_4_customers")
    assert result and all(r["Customers"] > 4 for r in result)
    counts = defaultdict(int)
    for r in rows(db, "SELECT Country FROM Customer"):
        counts[r["Country"]] += 1
    assert {r["Country"] for r in result} == {c for c, n in counts.items() if n > 4}


def test_average_track_length_per_album(db):
    result = run(db, "average_track_length_per_album")
    first = result[0]
    ms = [r["Milliseconds"] for r in rows(db, f"SELECT Milliseconds FROM Track WHERE AlbumId = {first['AlbumId']}")]
    assert first["Tracks"] == len(ms)
    assert first["AvgMinutes"] == pytest.approx(sum(ms) / len(ms) / 60000, abs=0.01)


# ── 04 subqueries ─────────────────────────────────────────────────────────────

def test_tracks_longer_than_average(db):
    ms = [r["Milliseconds"] for r in rows(db, "SELECT Milliseconds FROM Track")]
    avg = sum(ms) / len(ms)
    assert len(run(db, "tracks_longer_than_average")) == sum(1 for m in ms if m > avg)


def test_customers_above_average_spend(db):
    totals = defaultdict(float)
    for r in rows(db, "SELECT CustomerId, Total FROM Invoice"):
        totals[r["CustomerId"]] += r["Total"]
    avg = sum(totals.values()) / len(totals)
    expected = {c for c, t in totals.items() if round(t, 2) > avg}
    assert {r["CustomerId"] for r in run(db, "customers_above_average_spend")} == expected


def test_albums_with_more_than_20_tracks(db):
    counts = defaultdict(int)
    for r in rows(db, "SELECT AlbumId FROM Track WHERE AlbumId IS NOT NULL"):
        counts[r["AlbumId"]] += 1
    assert {r["AlbumId"] for r in run(db, "albums_with_more_than_20_tracks")} == {a for a, n in counts.items() if n > 20}


def test_sold_plus_never_sold_equals_all_tracks(db):
    sold = rows(db, "SELECT COUNT(DISTINCT TrackId) AS n FROM InvoiceLine")[0]["n"]
    never = len(run(db, "tracks_never_sold"))
    assert sold + never == rows(db, "SELECT COUNT(*) AS n FROM Track")[0]["n"]


def test_customers_without_invoices_is_consistent(db):
    with_invoices = rows(db, "SELECT COUNT(DISTINCT CustomerId) AS n FROM Invoice")[0]["n"]
    assert with_invoices + len(run(db, "customers_without_invoices")) == rows(db, "SELECT COUNT(*) AS n FROM Customer")[0]["n"]


def test_best_selling_genre_matches_python(db):
    units = defaultdict(int)
    for r in rows(db, "SELECT g.Name AS G, il.Quantity AS Q FROM InvoiceLine il JOIN Track t ON t.TrackId = il.TrackId JOIN Genre g ON g.GenreId = t.GenreId"):
        units[r["G"]] += r["Q"]
    best = max(units.values())
    result = run(db, "best_selling_genre_cte")
    assert len(result) == 1 and result[0]["UnitsSold"] == best and units[result[0]["Genre"]] == best


# ── 05 window functions ───────────────────────────────────────────────────────

def test_customer_rank_within_country(db):
    result = run(db, "customer_rank_within_country")
    assert len(result) == rows(db, "SELECT COUNT(DISTINCT CustomerId) AS n FROM Invoice")[0]["n"]
    by_country = defaultdict(list)
    for r in result:
        by_country[r["Country"]].append(r)
    for country, items in by_country.items():
        assert min(i["CountryRank"] for i in items) == 1, country
        top = max(i["TotalSpent"] for i in items)
        assert all(i["TotalSpent"] == top for i in items if i["CountryRank"] == 1), country


def test_running_revenue_is_monotonic_and_ends_at_total(db):
    result = run(db, "running_revenue_by_month")
    running = [r["RunningRevenue"] for r in result]
    assert running == sorted(running)
    total = rows(db, "SELECT SUM(Total) AS s FROM Invoice")[0]["s"]
    assert running[-1] == pytest.approx(total, abs=0.05)


def test_month_over_month_change(db):
    result = run(db, "month_over_month_change")
    assert result[0]["PrevRevenue"] is None and result[0]["Change"] is None
    for prev, cur in zip(result, result[1:]):
        assert cur["PrevRevenue"] == prev["Revenue"]
        assert cur["Change"] == pytest.approx(cur["Revenue"] - prev["Revenue"], abs=0.01)


def test_top_selling_track_per_genre_has_one_row_per_genre(db):
    result = run(db, "top_selling_track_per_genre")
    genres = [r["Genre"] for r in result]
    assert len(genres) == len(set(genres))
    sold_genres = rows(db, "SELECT COUNT(DISTINCT t.GenreId) AS n FROM InvoiceLine il JOIN Track t ON t.TrackId = il.TrackId")[0]["n"]
    assert len(genres) == sold_genres
