"""Test the import endpoint with realistic messy data."""
import requests
import sys

API_BASE = "http://localhost:8000/api"
TOKEN = None

def get_token():
    """Login and get a JWT token."""
    global TOKEN
    # Try to register first, then login
    resp = requests.post(f"{API_BASE}/auth/register", json={
        "email": "testimporter@example.com",
        "password": "testpassword123!",
        "full_name": "Test Importer"
    })
    resp = requests.post(f"{API_BASE}/auth/login", json={
        "email": "testimporter@example.com",
        "password": "testpassword123!"
    })
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        sys.exit(1)
    TOKEN = resp.json()["access_token"]
    print(f"Got token: {TOKEN[:20]}...")

def test_csv_import():
    print("\n=== TEST 1: CSV Import (messy data, dry_run=true) ===")
    with open("/root/.openclaw/workspace/ai-crm-swarm/backend/tests/test_import_messy.csv", "rb") as f:
        resp = requests.post(
            f"{API_BASE}/contacts/import",
            files={"file": ("test_import_messy.csv", f, "text/csv")},
            data={"dry_run": "true"},
            headers={"Authorization": f"Bearer {TOKEN}"}
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

def test_csv_real_import():
    print("\n=== TEST 2: CSV Import (dry_run=false, real write) ===")
    with open("/root/.openclaw/workspace/ai-crm-swarm/backend/tests/test_import_messy.csv", "rb") as f:
        resp = requests.post(
            f"{API_BASE}/contacts/import",
            files={"file": ("test_import_messy.csv", f, "text/csv")},
            data={"dry_run": "false"},
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Summary: imported={data['imported']}, skipped={data['skipped_duplicates']}, errors={data['errors']}")
    assert data['imported'] == 6, f"Expected 6 imported, got {data['imported']}"
    assert data['skipped_duplicates'] == 1
    assert data['errors'] == 3
    print("PASS")

def test_csv_second_run_dedupes():
    print("\n=== TEST 3: Re-import same file — all should be duplicates ===")
    with open("/root/.openclaw/workspace/ai-crm-swarm/backend/tests/test_import_messy.csv", "rb") as f:
        resp = requests.post(
            f"{API_BASE}/contacts/import",
            files={"file": ("test_import_messy.csv", f, "text/csv")},
            data={"dry_run": "false"},
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
    data = resp.json()
    print(f"Summary: imported={data['imported']}, skipped={data['skipped_duplicates']}, errors={data['errors']}")
    assert data['imported'] == 0, f"Expected 0 new, got {data['imported']}"
    assert data['skipped_duplicates'] == 7, f"Expected 7 duplicates, got {data['skipped_duplicates']}"
    print("PASS")

def test_xlsx_import():
    print("\n=== TEST 4: XLSX Import with alternate headers (dry_run=true) ===")
    with open("/root/.openclaw/workspace/ai-crm-swarm/backend/tests/test_import_messy.xlsx", "rb") as f:
        resp = requests.post(
            f"{API_BASE}/contacts/import",
            files={"file": ("test_import_messy.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"dry_run": "true"},
            headers={"Authorization": f"Bearer {TOKEN}"}
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
    get_token()
    test_csv_import()
    test_csv_real_import()
    test_csv_second_run_dedupes()
    test_xlsx_import()
    print("\n=== ALL TESTS PASSED ===")
