"""Test the import endpoint with realistic messy data.

Runs in-process via FastAPI's TestClient (see conftest.py); no live server
needed. The tests are order-dependent (real import, then dedupe check), which
pytest preserves within a file.
"""
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent
CSV_PATH = FIXTURES / "test_import_messy.csv"
XLSX_PATH = FIXTURES / "test_import_messy.xlsx"

def test_csv_import(client, auth_headers):
    print("\n=== TEST 1: CSV Import (messy data, dry_run=true) ===")
    with open(CSV_PATH, "rb") as f:
        resp = client.post(
            "/api/contacts/import",
            files={"file": ("test_import_messy.csv", f, "text/csv")},
            data={"dry_run": "true"},
            headers=auth_headers
        )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Summary: imported={data['imported']}, skipped={data['skipped_duplicates']}, errors={data['errors']}")
    print(f"Column map: {data['column_map']}")
    if data['row_errors']:
        print("Row errors:")
        for err in data['row_errors']:
            print(f"  Row {err['row_number']}: {err['errors']}")
    assert data['imported'] == 7, f"Expected 7 importable, got {data['imported']}"
    assert data['skipped_duplicates'] == 0, f"Expected 0 duplicates (fresh DB), got {data['skipped_duplicates']}"
    assert data['errors'] == 3, f"Expected 3 errors, got {data['errors']}"
    print("PASS")

def test_csv_real_import(client, auth_headers):
    print("\n=== TEST 2: CSV Import (dry_run=false, real write) ===")
    with open(CSV_PATH, "rb") as f:
        resp = client.post(
            "/api/contacts/import",
            files={"file": ("test_import_messy.csv", f, "text/csv")},
            data={"dry_run": "false"},
            headers=auth_headers
        )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Summary: imported={data['imported']}, skipped={data['skipped_duplicates']}, errors={data['errors']}")
    assert data['imported'] == 6, f"Expected 6 imported, got {data['imported']}"
    assert data['skipped_duplicates'] == 1
    assert data['errors'] == 3
    print("PASS")

def test_csv_second_run_dedupes(client, auth_headers):
    print("\n=== TEST 3: Re-import same file — all should be duplicates ===")
    with open(CSV_PATH, "rb") as f:
        resp = client.post(
            "/api/contacts/import",
            files={"file": ("test_import_messy.csv", f, "text/csv")},
            data={"dry_run": "false"},
            headers=auth_headers
        )
    data = resp.json()
    print(f"Summary: imported={data['imported']}, skipped={data['skipped_duplicates']}, errors={data['errors']}")
    assert data['imported'] == 0, f"Expected 0 new, got {data['imported']}"
    assert data['skipped_duplicates'] == 7, f"Expected 7 duplicates, got {data['skipped_duplicates']}"
    print("PASS")

def test_xlsx_import(client, auth_headers):
    print("\n=== TEST 4: XLSX Import with alternate headers (dry_run=true) ===")
    with open(XLSX_PATH, "rb") as f:
        resp = client.post(
            "/api/contacts/import",
            files={"file": ("test_import_messy.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"dry_run": "true"},
            headers=auth_headers
        )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Summary: imported={data['imported']}, skipped={data['skipped_duplicates']}, errors={data['errors']}")
    print(f"Column map: {data['column_map']}")
    assert data['imported'] == 3, f"Expected 3 importable, got {data['imported']}"
    assert data['skipped_duplicates'] == 0, f"Expected 0 duplicates (fresh DB), got {data['skipped_duplicates']}"
    assert data['errors'] == 1, f"Expected 1 error, got {data['errors']}"
    # Verify fuzzy mapping worked
    assert 'first_name' in data['column_map'], "Fuzzy mapping failed for first_name"
    assert data['column_map']['first_name'] == 'given name', f"Expected 'given name', got {data['column_map']['first_name']}"
    print("PASS")

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
