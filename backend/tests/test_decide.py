"""골든 아웃풋 G1~G7 + 공통 게이트 (PROJECT_SPEC §11).

headline·steps는 문자열 그대로, analysis_bullets는 해당 문구 포함 여부로 검사한다.
"""

import json
from pathlib import Path

import pytest

from app.models import Observation
from app.services import decide as decide_module
from app.services.decide import decide

FIXTURES = Path(__file__).parent / "fixtures"
REGION = {"sido": "부산광역시", "gu": "해운대구"}


def obs(name: str, **overrides) -> Observation:
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    data.update(overrides)
    return Observation.model_validate(data)


def assert_bullets(decision, expected: list[str]) -> None:
    for b in expected:
        assert b in decision.analysis_bullets, f"{b!r} not in {decision.analysis_bullets}"
    assert len(decision.analysis_bullets) <= 4


def test_g1_pet_clear():
    d = decide(obs("pet_clear_label"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "PET_CLEAR")
    assert d.headline == "투명 페트병 별도배출 대상입니다."
    assert_bullets(d, ["페트병 (투명)", "라벨 부착 있음", "내용물 없음", "파손 없음"])
    assert d.steps == ["내용물을 완전히 비우고 헹구기", "라벨 제거하기", "찌그러뜨리고 뚜껑 닫아 투명 페트병 전용 수거함에 배출하기"]
    assert d.terminal


def test_g2_styrofoam_sauce_asks_question():
    d = decide(obs("styrofoam_sauce"), REGION, None, 1)
    assert d.kind == "ASK_QUESTION"
    assert d.question is not None
    assert d.question.text == "이물질을 제거할 수 있나요?"
    assert [o.l for o in d.question.options] == [
        "네, 제거할 수 있어요",
        "아니요, 제거할 수 없어요",
        "잘 모르겠어요",
    ]
    assert not d.terminal


@pytest.mark.parametrize("answer", ["no", "unknown"])
def test_g3_path_b_general(answer):
    d = decide(obs("styrofoam_sauce"), REGION, {"contamination_removable": answer}, 1)
    assert (d.kind, d.result_code) == ("FINAL", "GENERAL")
    assert d.headline == "일반폐기물 배출 대상입니다."
    assert_bullets(d, ["스티로폼 용기", "음식물·소스 오염 있음", "오염 제거 어려움 (사용자 답변)"])
    assert d.steps == ["내용물을 비우고", "오염 제거가 어려우면 재활용 제외", "종량제 봉투에 넣어 배출하기"]
    assert d.terminal


def test_g4_path_a_wash_and_reshoot():
    d = decide(obs("styrofoam_sauce"), REGION, {"contamination_removable": "yes"}, 1)
    assert d.kind == "WASH_AND_RESHOOT"
    assert d.headline == "세척 후 다시 촬영해주세요."
    assert d.wash_checklist == ["남은 음식물 제거", "물로 깨끗이 헹구기", "이물질이 남지 않도록 세척하기"]
    assert not d.terminal


def test_g5_reshoot_clean_styrofoam():
    d = decide(obs("styrofoam_clean"), REGION, None, 2)
    assert (d.kind, d.result_code) == ("FINAL", "STYROFOAM")
    assert d.headline == "스티로폼류 분리배출 대상입니다."
    assert_bullets(d, ["스티로폼 용기", "음식물·소스 오염 없음 (세척 완료)", "파손 없음"])
    assert d.steps == ["내용물을 완전히 비우고 세척하기", "테이프·운송장 제거하기", "스티로폼류로 분리배출하기"]


def test_g5b_reshoot_still_dirty_is_general():
    d = decide(obs("styrofoam_sauce"), REGION, None, 2)
    assert (d.kind, d.result_code) == ("FINAL", "GENERAL")
    assert "세척 후에도 오염이 남아 있음" in d.analysis_bullets


def test_g6_plastic_pp_clean():
    d = decide(obs("plastic_pp_clean"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "PLASTIC")
    assert d.headline == "플라스틱류 분리배출 대상입니다."
    assert_bullets(d, ["플라스틱 배달 용기(PP 추정)", "오염 없음 (깨끗함)", "라벨·부착물 없음", "파손 없음"])
    assert d.steps == ["내용물 비우기", "라벨·스티커 제거하기", "플라스틱류로 분리배출하기"]


def test_g7_cardboard_tape():
    d = decide(obs("cardboard_tape"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "PAPER")
    assert d.headline == "종이류 분리배출 대상입니다."
    assert_bullets(d, ["종이상자 (골판지)", "테이프 부착 있음", "오염 없음, 재활용 가능"])
    assert d.steps == ["테이프·송장 제거하기", "상자를 펼쳐 납작하게 하기", "종이류로 분리배출하기"]


# ---------- 공통 게이트 ----------


def test_gate_blurry_photo():
    d = decide(obs("pet_clear_label", photo_quality="blurry"), REGION, None, 1)
    assert (d.kind, d.reshoot_reason) == ("RESHOOT_QUALITY", "quality")


def test_gate_low_confidence():
    d = decide(obs("pet_clear_label", confidence=0.4), REGION, None, 1)
    assert (d.kind, d.reshoot_reason) == ("RESHOOT_QUALITY", "quality")


def test_gate_privacy_wins_over_quality():
    d = decide(obs("cardboard_tape", privacy_flag=True, photo_quality="dark"), REGION, None, 1)
    assert (d.kind, d.reshoot_reason) == ("RESHOOT_QUALITY", "privacy")


def test_gate_unknown_item():
    d = decide(obs("pet_clear_label", item_type="other"), REGION, None, 1)
    assert d.kind == "UNKNOWN"
    assert d.terminal


# ---------- 검증 여부 표시 (§9.3, §13) ----------


def test_verified_rules_basis_label_and_official_url():
    d = decide(obs("pet_clear_label"), REGION, None, 1)
    assert d.rules_verified is True
    assert d.basis_label == "부산광역시 2026년 기준"
    assert d.source.url is not None and d.source.url.startswith("https://www.busan.go.kr/")


def test_unverified_rules_hide_url(monkeypatch):
    rules = {**decide_module.load_rules(), "busan_verified": False}
    monkeypatch.setattr(decide_module, "load_rules", lambda: rules)
    d = decide(obs("pet_clear_label"), REGION, None, 1)
    assert d.rules_verified is False
    assert d.basis_label == "시연용 규칙 기준"
    assert d.source.url is None


def test_gate_reason_shared_with_observe():
    # /api/observe가 같은 함수로 ok/reason을 판정하므로 decide 결과와 어긋나지 않아야 한다
    assert decide_module.gate_reason(obs("pet_clear_label")) is None
    assert decide_module.gate_reason(obs("pet_clear_label", confidence=0.59)) == "quality"
    assert decide_module.gate_reason(obs("pet_clear_label", privacy_flag=True, photo_quality="dark")) == "privacy"


# ---------- 확장: 캔 (부산시 캔류·고철 안내) ----------


def test_g8_can():
    d = decide(obs("can_empty"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "CAN")
    assert d.headline == "캔류 분리배출 대상입니다."
    assert d.analysis_bullets == ["캔 (금속)", "내용물 없음", "파손 없음"]
    assert d.steps == ["내용물을 비우고 헹구기", "플라스틱 뚜껑 등 다른 재질은 분리하기", "캔류로 분리배출하기"]
    assert d.source.url is not None


def test_can_with_contents_still_can():
    # 내용물이 남아 있어도 헹구면 되므로 질문 없이 캔류로 안내한다
    d = decide(obs("can_empty", contents_present="yes"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "CAN")
    assert "내용물 있음" in d.analysis_bullets
