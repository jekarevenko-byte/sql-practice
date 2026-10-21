"""
Pattern: after an API operation, verify that the DB holds the same data.
Here the "API response" is a JSON fixture; in a real project it would come from
the requests-based client of the API tests project (qa_api_tests).
"""

import json
from pathlib import Path

import pytest

from src.compare import assert_api_matches_db

FIXTURE = Path(__file__).parent / "fixtures" / "invoice_1_api_response.json"
FIELD_MAP = {
    "invoiceId": "InvoiceId",
    "customerId": "CustomerId",
    "billingCountry": "BillingCountry",
    "total": "Total",
}


@pytest.fixture
def api_body() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def db_invoice(db, invoice_id: int):
    return db.execute("SELECT * FROM Invoice WHERE InvoiceId = ?", (invoice_id,)).fetchone()


def test_api_response_matches_database(db, api_body):
    assert_api_matches_db(api_body, db_invoice(db, api_body["invoiceId"]), FIELD_MAP)


def test_helper_reports_all_differences_at_once(db, api_body):
    api_body["total"] = 99.99
    api_body["billingCountry"] = "France"
    with pytest.raises(AssertionError) as exc:
        assert_api_matches_db(api_body, db_invoice(db, 1), FIELD_MAP)
    message = str(exc.value)
    assert "total" in message and "billingCountry" in message


def test_helper_reports_missing_api_field(db, api_body):
    del api_body["customerId"]
    with pytest.raises(AssertionError, match="customerId"):
        assert_api_matches_db(api_body, db_invoice(db, 1), FIELD_MAP)


def test_float_tolerance(db, api_body):
    api_body["total"] = 1.9800001  # float noise must not fail the comparison
    assert_api_matches_db(api_body, db_invoice(db, 1), FIELD_MAP)
