"""Supabase 익명 로그. 실패해도 요청을 실패시키지 않는다(CLAUDE.md §6, PROJECT_SPEC §7.3).

이미지·식별자·IP는 넣지 않는다. SUPABASE_URL/SERVICE_ROLE_KEY가 없으면 조용히 건너뛴다.
"""

import os

from supabase import Client, ClientOptions, create_client

TIMEOUT_S = 1.5

_client: Client | None = None


def _get_client() -> Client | None:
    global _client
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    if _client is None:
        _client = create_client(url, key, options=ClientOptions(postgrest_client_timeout=TIMEOUT_S))
    return _client


def log_decision(
    *,
    gu: str | None,
    item_type: str | None,
    kind: str,
    result_code: str | None,
    attempt: int | None,
    photo_quality: str | None,
    privacy_flag: bool | None,
    rules_verified: bool | None,
    demo_mode: bool,
) -> None:
    """analysis_logs(부록 B)에 1행 추가. 어떤 예외도 밖으로 내보내지 않는다."""
    try:
        client = _get_client()
        if client is None:
            return
        client.table("analysis_logs").insert(
            {
                "gu": gu,
                "item_type": item_type,
                "kind": kind,
                "result_code": result_code,
                "attempt": attempt,
                "photo_quality": photo_quality,
                "privacy_flag": privacy_flag,
                "rules_verified": rules_verified,
                "demo_mode": demo_mode,
            }
        ).execute()
    except Exception:  # noqa: BLE001 — 로깅 실패는 요청에 영향을 주지 않는다
        return
