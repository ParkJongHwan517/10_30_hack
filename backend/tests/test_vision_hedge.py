"""vision.observe의 헤징(느린 첫 호출 대신 둘째 호출을 쓰는 동작) 단위 테스트. Gemini를 호출하지 않는다."""

import time
from pathlib import Path

import pytest

from app.models import Observation
from app.services import vision

FIXTURES = Path(__file__).parent / "fixtures"
OBS = Observation.model_validate_json((FIXTURES / "pet_clear_label.json").read_text(encoding="utf-8"))


class Busy(Exception):
    """vision._is_busy가 '지연/쿼터'로 보는 예외 대신 쓰는 가짜 예외."""


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(vision, "HEDGE_AFTER_S", 0.2)
    monkeypatch.setattr(vision, "RETRY_DELAY_S", 0.01)
    monkeypatch.setattr(vision, "_is_busy", lambda exc: isinstance(exc, Busy))


def script(monkeypatch, steps):
    """호출 순서대로 (지연 초, 결과 또는 예외)를 돌려주는 가짜 _call."""
    calls = []

    def fake(image_bytes, mime_type, timeout_ms):
        i = len(calls)
        calls.append(timeout_ms)
        delay, result = steps[min(i, len(steps) - 1)]
        time.sleep(delay)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(vision, "_call", fake)
    return calls


def test_fast_first_call_is_used_without_hedge(monkeypatch):
    calls = script(monkeypatch, [(0.0, [OBS])])
    assert vision.observe(b"x")[0].item_type == "pet_bottle"
    assert len(calls) == 1


def test_slow_first_call_is_beaten_by_hedge(monkeypatch):
    calls = script(monkeypatch, [(2.0, [OBS]), (0.05, [OBS])])
    t = time.monotonic()
    assert vision.observe(b"x")
    assert time.monotonic() - t < 1.0  # 첫 호출(2초)을 기다리지 않는다
    assert len(calls) == 2


def test_fast_busy_failure_retries_once(monkeypatch):
    calls = script(monkeypatch, [(0.0, Busy()), (0.0, [OBS])])
    assert vision.observe(b"x")
    assert len(calls) == 2


def test_both_busy_raises_visionbusy(monkeypatch):
    script(monkeypatch, [(0.0, Busy()), (0.0, Busy())])
    with pytest.raises(vision.VisionBusy):
        vision.observe(b"x")


def test_non_busy_error_is_visionfailed(monkeypatch):
    script(monkeypatch, [(0.0, ValueError("boom"))])
    with pytest.raises(vision.VisionFailed):
        vision.observe(b"x")


def test_bad_replies_fall_back_to_reshoot_item(monkeypatch):
    script(monkeypatch, [(0.0, None), (0.0, None)])
    items = vision.observe(b"x")
    assert len(items) == 1 and items[0].photo_quality == "partial" and items[0].confidence == 0.0


def test_confidence_is_clamped_and_items_capped(monkeypatch):
    many = [OBS.model_copy(update={"confidence": 1.7}) for _ in range(9)]
    script(monkeypatch, [(0.0, many)])
    items = vision.observe(b"x")
    assert len(items) == vision.MAX_ITEMS and all(o.confidence == 1.0 for o in items)
