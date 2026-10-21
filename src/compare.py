"""Pattern for "check data in the DB after an API call": compare an API JSON body with a DB row."""

from typing import Any, Mapping


def assert_api_matches_db(
    api_body: Mapping[str, Any],
    db_row: Mapping[str, Any],
    field_map: Mapping[str, str],
    float_tolerance: float = 0.005,
) -> None:
    """
    Compare fields of an API response with the corresponding DB columns.

    field_map: {api_field: db_column}. All mismatches are collected and reported
    together, so one failed run shows every difference, not only the first one.
    """
    problems: list[str] = []
    for api_field, db_column in field_map.items():
        if api_field not in api_body:
            problems.append(f"API field '{api_field}' is missing")
            continue
        if db_column not in db_row.keys():
            problems.append(f"DB column '{db_column}' is missing")
            continue
        api_value, db_value = api_body[api_field], db_row[db_column]
        if isinstance(api_value, (int, float)) and isinstance(db_value, (int, float)):
            equal = abs(api_value - db_value) <= float_tolerance
        else:
            equal = api_value == db_value
        if not equal:
            problems.append(f"{api_field}: API={api_value!r} but DB.{db_column}={db_value!r}")
    assert not problems, "API and DB differ:\n  " + "\n  ".join(problems)
