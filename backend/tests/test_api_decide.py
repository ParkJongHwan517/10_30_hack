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
