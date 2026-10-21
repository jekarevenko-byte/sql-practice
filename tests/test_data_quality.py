"""
Data-quality checks (SQL in sql/06_data_validation.sql).

1. On the real database every check must return zero violations.
2. On a deliberately damaged copy every check must FIND the defect —
   a check that can never fail is worthless.
"""

import pytest

from src.sql_loader import run

CLEAN_CHECKS = [
    "invoice_total_differs_from_lines",
    "invoices_without_lines",
    "orphan_invoice_lines",
    "orphan_invoices",
    "orphan_tracks",
    "tracks_without_album",
    "tracks_without_genre",
    "duplicate_customer_emails",
    "customers_with_invalid_email",
    "non_positive_values",
    "employees_with_missing_manager",
    "customers_with_missing_support_rep",
    "playlist_track_orphans",
    "duplicate_artist_names",
    "invoices_dated_in_future",
]


@pytest.mark.parametrize("check", CLEAN_CHECKS)
def test_real_database_has_no_violations(db, check):
    violations = run(db, check)
    assert violations == [], f"{check}: {len(violations)} violation(s), first: {dict(violations[0])}"


# (check name, SQL that injects the defect)
DEFECTS = [
    ("invoice_total_differs_from_lines", "UPDATE Invoice SET Total = Total + 10 WHERE InvoiceId = 1"),
    ("invoices_without_lines", "DELETE FROM InvoiceLine WHERE InvoiceId = 1"),
    ("orphan_invoice_lines", "DELETE FROM Track WHERE TrackId = 2"),
    ("orphan_invoices", "DELETE FROM Customer WHERE CustomerId = 2"),
    ("orphan_tracks", "DELETE FROM Album WHERE AlbumId = 1"),
    ("tracks_without_album", "UPDATE Track SET AlbumId = NULL WHERE TrackId = 1"),
    ("tracks_without_genre", "UPDATE Track SET GenreId = NULL WHERE TrackId = 1"),
    ("duplicate_customer_emails", "UPDATE Customer SET Email = (SELECT Email FROM Customer WHERE CustomerId = 1) WHERE CustomerId = 2"),
    ("customers_with_invalid_email", "UPDATE Customer SET Email = 'not-an-email' WHERE CustomerId = 1"),
    ("non_positive_values", "UPDATE Track SET UnitPrice = -1 WHERE TrackId = 1"),
    ("employees_with_missing_manager", "UPDATE Employee SET ReportsTo = 999 WHERE EmployeeId = 2"),
    ("customers_with_missing_support_rep", "UPDATE Customer SET SupportRepId = 999 WHERE CustomerId = 1"),
    ("playlist_track_orphans", "INSERT INTO PlaylistTrack (PlaylistId, TrackId) VALUES (9999, 1)"),
    ("duplicate_artist_names", "INSERT INTO Artist (ArtistId, Name) VALUES (99999, (SELECT Name FROM Artist WHERE ArtistId = 1))"),
    ("invoices_dated_in_future", "UPDATE Invoice SET InvoiceDate = '2999-01-01 00:00:00' WHERE InvoiceId = 1"),
]


@pytest.mark.parametrize("check, defect_sql", DEFECTS, ids=[d[0] for d in DEFECTS])
def test_check_detects_injected_defect(broken_db, check, defect_sql):
    assert run(broken_db, check) == [], "precondition: the copy must start clean (or this defect is already present)"
    broken_db.execute(defect_sql)
    assert len(run(broken_db, check)) >= 1, f"{check} did not detect the injected defect"


def test_every_validation_check_is_covered():
    """Guard: adding a new check to the SQL file without a test should fail here."""
    from src.sql_loader import QUERIES

    validation = {n for n in QUERIES if n in CLEAN_CHECKS}
    assert set(CLEAN_CHECKS) == validation, "CLEAN_CHECKS contains a query that does not exist"
    assert {d[0] for d in DEFECTS} == set(CLEAN_CHECKS), "every check needs a defect-injection case"
