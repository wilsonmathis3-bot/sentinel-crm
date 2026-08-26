"""EOD Sweep — daily health checks and CRM login verification.
Pure HTTP, no outbound messages, no LLM calls.
"""
import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
import httpx

from sqlalchemy.orm import Session
from app import models

# --- Config from env ---
EOD_CRM_API_URL = os.getenv("EOD_CRM_API_URL", "https://crm-api-production-4087.up.railway.app")
EOD_CRM_WEB_URL = os.getenv("EOD_CRM_WEB_URL", "https://crm-web-production-7065.up.railway.app")
EOD_SENTINEL_SELF_URL = os.getenv("EOD_SENTINEL_SELF_URL", "https://sentinel-production-adc5.up.railway.app")
EOD_BOS_SITE_URL = os.getenv("EOD_BOS_SITE_URL", "https://bos-site-production.up.railway.app")
EOD_CRM_TEST_EMAIL = os.getenv("EOD_CRM_TEST_EMAIL", "")
EOD_CRM_TEST_PASSWORD = os.getenv("EOD_CRM_TEST_PASSWORD", "")
EOD_REQUEST_TIMEOUT = float(os.getenv("EOD_REQUEST_TIMEOUT", "15.0"))


async def _check_http(url: str, client: httpx.AsyncClient, method: str = "GET",
                       payload: Dict = None, expected_status: int = 200) -> Dict[str, Any]:
    """Generic HTTP check with timing and status capture."""
    result = {
        "url": url,
        "method": method,
        "expected_status": expected_status,
        "actual_status": None,
        "response_time_ms": None,
        "error": None,
        "ok": False,
    }
    start = datetime.now(timezone.utc)
    try:
        if method.upper() == "POST" and payload is not None:
            response = await client.post(url, json=payload, timeout=EOD_REQUEST_TIMEOUT)
        else:
            response = await client.get(url, timeout=EOD_REQUEST_TIMEOUT)
        elapsed = datetime.now(timezone.utc) - start
        result["response_time_ms"] = round(elapsed.total_seconds() * 1000, 2)
        result["actual_status"] = response.status_code
        result["ok"] = response.status_code == expected_status
        try:
            result["body_preview"] = response.text[:200]
        except Exception:
            result["body_preview"] = ""
    except httpx.TimeoutException:
        result["error"] = "timeout"
    except httpx.ConnectError as e:
        result["error"] = f"connect_error: {str(e)}"
    except Exception as e:
        result["error"] = f"exception: {str(e)}"
    return result


async def _crm_login_roundtrip(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Perform a full CRM login round trip using test credentials from env."""
    result = {
        "check": "crm_login_roundtrip",
        "ok": False,
        "steps": {},
        "error": None,
    }

    login_url = f"{EOD_CRM_API_URL.rstrip('/')}/auth/login"
    login_payload = {
        "email": EOD_CRM_TEST_EMAIL,
        "password": EOD_CRM_TEST_PASSWORD,
    }
    login_check = await _check_http(login_url, client, method="POST",
                                     payload=login_payload, expected_status=200)
    result["steps"]["login"] = login_check

    if not login_check["ok"]:
        result["error"] = "login_failed"
        return result

    token = None
    try:
        body = json.loads(login_check.get("body_preview", "{}"))
        token = body.get("token") or body.get("access_token")
    except Exception:
        pass

    if not token:
        result["error"] = "no_token_in_response"
        return result

    verify_url = f"{EOD_CRM_API_URL.rstrip('/')}/auth/me"
    verify_check = await _check_http(verify_url, client, expected_status=200)
    verify_check["headers_sent"] = {"Authorization": "Bearer ***"}
    result["steps"]["verify_session"] = verify_check

    if verify_check["ok"]:
        result["ok"] = True

    return result


async def run_eod_sweep(db: Session) -> Dict[str, Any]:
    """Run the full EOD sweep and persist results."""
    sweep_ts = datetime.now(timezone.utc).isoformat()
    checks: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # 1. CRM API health
        crm_api_health = await _check_http(
            f"{EOD_CRM_API_URL.rstrip('/')}/health", client
        )
        crm_api_health["service"] = "crm_api"
        checks.append(crm_api_health)

        # 2. CRM Web (root page, expect 200)
        crm_web_check = await _check_http(EOD_CRM_WEB_URL, client)
        crm_web_check["service"] = "crm_web"
        checks.append(crm_web_check)

        # 3. Sentinel self (health endpoint)
        sentinel_check = await _check_http(
            f"{EOD_SENTINEL_SELF_URL.rstrip('/')}/api/health", client
        )
        sentinel_check["service"] = "sentinel"
        checks.append(sentinel_check)

        # 4. BOS Site
        bos_check = await _check_http(EOD_BOS_SITE_URL, client)
        bos_check["service"] = "bos_site"
        checks.append(bos_check)

        # 5. CRM login round trip (only if credentials configured)
        if EOD_CRM_TEST_EMAIL and EOD_CRM_TEST_PASSWORD:
            login_result = await _crm_login_roundtrip(client)
            login_result["service"] = "crm_login"
            checks.append(login_result)
        else:
            checks.append({
                "service": "crm_login",
                "ok": None,
                "note": "skipped: no test credentials configured",
            })

    total = len([c for c in checks if c.get("ok") is not None])
    passed = len([c for c in checks if c.get("ok") is True])
    failed = len([c for c in checks if c.get("ok") is False])

    sweep_record = {
        "swept_at": sweep_ts,
        "summary": {
            "total_checked": total,
            "passed": passed,
            "failed": failed,
            "all_healthy": failed == 0 and total > 0,
        },
        "checks": checks,
    }

    # Persist to DB
    db_sweep = models.EodSweep(
        swept_at=datetime.now(timezone.utc),
        summary=json.dumps(sweep_record["summary"]),
        checks=json.dumps(sweep_record["checks"]),
    )
    db.add(db_sweep)
    db.commit()
    db.refresh(db_sweep)

    return sweep_record
