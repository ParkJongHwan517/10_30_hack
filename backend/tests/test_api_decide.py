"""/api/decide 엔드포인트가 규칙 엔진 결과를 그대로 돌려주는지 확인 (G2→G4 경로 A)."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SAUCE = json.loads((Path(__file__).parent / "fixtures" / "styrofoam_sauce.json").read_text(encoding="utf-8"))


def post(**body):
    return client.post("/api/decide", json={"region": {"sido": "부산광역시", "gu": "해운대구"}, "observation": SAUCE, **body})


def test_decide_ask_then_wash():
    r = post(attempt=1)
    assert r.status_code == 200
    assert r.json()["kind"] == "ASK_QUESTION"

    r = post(attempt=1, answers={"contamination_removable": "yes"})
    assert r.status_code == 200
    assert r.json()["kind"] == "WASH_AND_RESHOOT"


def test_decide_rejects_invalid_region():
    r = client.post(
        "/api/decide",
        json={"region": {"sido": "부산광역시", "gu": "강남구"}, "observation": SAUCE, "attempt": 1},
    )
    assert r.status_code == 422


def test_logs_only_terminal_results(monkeypatch):
    from app.routers import decide as decide_router

    calls = []
    monkeypatch.setattr(decide_router, "log_decision", lambda **kw: calls.append(kw))

    post(attempt=1)  # ASK_QUESTION → 기록 안 함
    assert calls == []

    post(attempt=1, answers={"contamination_removable": "no"}, demo_mode=True)  # FINAL → 1행
    assert len(calls) == 1
    assert calls[0] == {
        "gu": "해운대구",
        "item_type": "styrofoam_container",
        "kind": "FINAL",
        "result_code": "GENERAL",
        "attempt": 1,
        "photo_quality": "good",
        "privacy_flag": False,
        "rules_verified": True,
        "demo_mode": True,
    }


def test_decide_works_without_supabase(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    r = post(attempt=1, answers={"contamination_removable": "no"})
    assert r.status_code == 200
    assert r.json()["kind"] == "FINAL"
