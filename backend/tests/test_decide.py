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
    assert_bullets(d, ["플라스틱 용기 (PP 추정)", "오염 없음 (깨끗함)", "라벨·부착물 없음", "파손 없음"])
    assert d.steps == ["내용물 비우기", "라벨·스티커 제거하기", "플라스틱류로 분리배출하기"]


def test_g7_cardboard_tape():
    d = decide(obs("cardboard_tape"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "PAPER")
    assert d.headline == "종이류 분리배출 대상입니다."
    assert_bullets(d, ["종이상자", "테이프 부착 있음", "오염 없음, 재활용 가능"])
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


# ---------- 확장: 비닐·유리병·종이 보완 (부산시 2026 안내) ----------


def test_g9_vinyl_clean():
    d = decide(obs("vinyl_clean"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "VINYL")
    assert d.headline == "비닐류 분리배출 대상입니다."
    assert d.analysis_bullets == ["비닐류", "이물질 없음"]


def test_vinyl_dirty_is_general():
    dirty = {"level": "light", "type": "food", "likely_removable_by_rinsing": "unknown"}
    d = decide(obs("vinyl_clean", contamination=dirty), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "GENERAL")
    assert "이물질 묻음" in d.analysis_bullets


def test_g10_glass_bottle():
    d = decide(obs("glass_bottle_empty"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "GLASS")
    assert d.headline == "유리병류 분리배출 대상입니다."
    assert d.analysis_bullets == ["유리병", "내용물 없음", "파손 없음"]


def test_broken_glass_is_noncombustible():
    d = decide(obs("glass_bottle_empty", damage="broken"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "NONCOMBUSTIBLE")
    assert d.headline == "불연성 쓰레기 배출 대상입니다."
    assert "깨짐 있음" in d.analysis_bullets


def test_other_paper_falls_back_to_paper():
    # 과자 상자·종이 용기를 AI가 other로 내도 재질이 종이면 종이류
    d = decide(obs("cardboard_tape", item_type="other"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "PAPER")
    assert d.analysis_bullets[0] == "종이류"


def test_other_paper_with_food_is_general():
    soiled = {"level": "light", "type": "oil", "likely_removable_by_rinsing": "unknown"}
    d = decide(obs("cardboard_tape", item_type="other", contamination=soiled), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "GENERAL")


def test_other_non_paper_still_unknown():
    d = decide(obs("pet_clear_label", item_type="other", material_guess="PP"), REGION, None, 1)
    assert d.kind == "UNKNOWN"


# ---------- 여러 항목 (복합 쓰레기) ----------


def items(name: str) -> list[Observation]:
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    return [Observation.model_validate(o) for o in data]


def test_straw_is_general_with_moe_source():
    d = decide(obs("straw"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "GENERAL")
    assert d.steps == ["크기가 작아 재활용 선별이 되지 않아요", "종량제 봉투에 넣어 배출하기"]
    assert d.source.label.startswith("서울시 ")
    assert d.analysis_bullets[0] == "작은 플라스틱 (빨대·일회용 숟가락·포크 등)"


def test_coffee_cup_each_item():
    # 프론트가 항목마다 /api/decide를 부르는 방식과 같게, 항목별로 decide
    got = [(o.label_ko, decide(o, REGION, None, 1).result_code) for o in items("multi_coffee_cup")]
    assert got == [("컵 본체", "PLASTIC"), ("컵 뚜껑", "PLASTIC"), ("종이 컵홀더", "PAPER"), ("빨대", "GENERAL")]


def test_photo_gate_privacy_any_item():
    cup = items("multi_coffee_cup")
    cup[3] = cup[3].model_copy(update={"privacy_flag": True})
    assert decide_module.photo_gate_reason(cup) == "privacy"


def test_photo_gate_ignores_low_confidence_small_item():
    cup = items("multi_coffee_cup")
    cup[3] = cup[3].model_copy(update={"confidence": 0.3})
    assert decide_module.photo_gate_reason(cup) is None
    # 그 항목은 항목별 decide에서만 다시 찍기
    assert decide(cup[3], REGION, None, 1).kind == "RESHOOT_QUALITY"


def test_photo_gate_main_item_quality_and_empty():
    cup = items("multi_coffee_cup")
    cup[0] = cup[0].model_copy(update={"photo_quality": "blurry"})
    assert decide_module.photo_gate_reason(cup) == "quality"
    assert decide_module.photo_gate_reason([]) == "quality"


# ---------- 종이팩·영수증 (부산시 종이류 안내) ----------


def test_g11_paper_pack():
    d = decide(obs("paper_pack_milk"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "PAPER_PACK")
    assert d.headline == "종이팩 분리배출 대상입니다."
    assert d.analysis_bullets == ["종이팩 (우유·주스팩)", "내용물 없음"]
    assert d.steps[1] == "종이류와 섞지 말고 따로 모으기"


def test_receipt_is_general_not_paper():
    # 재질이 종이여도 영수증·코팅지는 종이류가 아니라 종량제
    d = decide(obs("receipt"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "GENERAL")
    assert d.steps == ["영수증·전표·코팅된 종이는 종이류로 재활용되지 않아요", "종량제 봉투에 넣어 배출하기"]
    assert d.source.label == "부산광역시 종이류 재활용품 분리배출 안내"
    assert d.analysis_bullets[0] == "영수증·코팅된 종이"


def test_non_box_paper_uses_general_paper_steps():
    # 컵홀더(other/paper)에 "상자를 펼쳐" 같은 상자 전용 문구가 나오지 않게
    d = decide(obs("cardboard_tape", item_type="other"), REGION, None, 1)
    assert d.result_code == "PAPER"
    assert d.steps == ["테이프·스프링 등 종이가 아닌 재질 제거하기", "이물질이 섞이지 않게 모으기", "종이류로 분리배출하기"]
    # 상자는 기존 문구 유지
    assert "상자를 펼쳐 납작하게 하기" in decide(obs("cardboard_tape"), REGION, None, 1).steps


def test_cardboard_box_item_named_holder_uses_general_paper_text():
    # 실제 Gemini가 종이 컵홀더를 cardboard_box로 내는 경우 — 상자 문구가 나오면 안 된다
    d = decide(obs("cardboard_tape", label_ko="종이 컵홀더"), REGION, None, 1)
    assert d.result_code == "PAPER"
    assert d.analysis_bullets[0] == "종이 컵홀더"
    assert d.steps == ["테이프·스프링 등 종이가 아닌 재질 제거하기", "이물질이 섞이지 않게 모으기", "종이류로 분리배출하기"]
    # 이름에 상자가 들어가거나 이름이 없으면 기존 상자 문구
    assert decide(obs("cardboard_tape", label_ko="택배 상자"), REGION, None, 1).steps[1] == "상자를 펼쳐 납작하게 하기"


def test_small_plastic_source_is_the_verified_one():
    d = decide(obs("straw"), REGION, None, 1)
    assert d.source.url == "https://mediahub.seoul.go.kr/archives/2003449"
    assert "부산시 안내에 없는" in d.source.label


# ---------- 일반쓰레기·불연성 확장 (부산시 종이류·불연성 안내, 인천시 물티슈) ----------


def test_wet_tissue_is_general_with_incheon_source():
    d = decide(obs("wet_tissue"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "GENERAL")
    assert d.analysis_bullets == ["물티슈"]
    assert d.steps[1] == "사용한 물티슈는 종량제 봉투에 넣어 배출하기"
    assert d.source.label == "인천시 안내 참고 (부산시 안내에 없는 품목)"
    assert d.source.url == "https://www.incheon.go.kr/infohub/HUB060901/3083791"


def test_general_waste_diaper_uses_busan_source():
    d = decide(obs("diaper"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "GENERAL")
    assert d.analysis_bullets == ["기저귀"]
    assert d.steps == ["재활용되지 않는 일반쓰레기예요", "종량제 봉투에 넣어 배출하기"]
    assert d.source.url == "https://www.busan.go.kr/depart/ahwastepolicy09"


def test_noncombustible_ceramic():
    d = decide(obs("ceramic_bowl"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "NONCOMBUSTIBLE")
    assert d.headline == "불연성 쓰레기 배출 대상입니다."
    assert d.analysis_bullets == ["사기그릇"]
    assert d.steps[1] == "불연성 전용 종량제 마대에 담기"


def test_unlisted_general_waste_stays_unknown():
    # 근거를 확인하지 못한 품목(마스크·칫솔 등)은 지어내지 않고 판단 불가
    d = decide(obs("wet_tissue", item_type="other", material_guess="PP"), REGION, None, 1)
    assert d.kind == "UNKNOWN"


# ---------- 구·군별 안내 (팀 조사 기준, 부산시 공식 판단과 분리) ----------


def test_district_info_attached_for_final_with_category():
    d = decide(obs("pet_clear_label"), REGION, None, 1)
    info = d.district_info
    assert info is not None and info.gu == "해운대구"
    assert info.verified is False and info.source_url is None
    assert info.source_label == "해운대구 안내 (팀 조사 기준, 공식 링크 없음 — 구청 안내를 확인하세요)"
    assert d.result_code == "PET_CLEAR" and d.headline == "투명 페트병 별도배출 대상입니다."  # 공식 판단은 그대로


def test_district_info_paper_pack_and_noncombustible_mapped():
    assert decide(obs("paper_pack_milk"), REGION, None, 1).district_info is not None
    assert decide(obs("glass_bottle_empty", damage="broken"), REGION, None, 1).district_info is not None


def test_district_info_none_for_general_and_non_final():
    assert decide(obs("styrofoam_sauce"), REGION, {"contamination_removable": "no"}, 1).district_info is None  # GENERAL
    assert decide(obs("styrofoam_sauce"), REGION, None, 1).district_info is None  # ASK_QUESTION
    assert decide(obs("wet_tissue"), REGION, None, 1).district_info is None


def test_district_info_never_exposes_disposal_method():
    info = decide(obs("pet_clear_label"), REGION, None, 1).district_info
    assert set(info.model_dump()) == {"gu", "prohibited_items", "special_notes", "verified", "source_label", "source_url"}


def test_strip_schedule_removes_weekday_sentences_only():
    assert decide_module.strip_schedule("수요일 문전 배출") == ""
    assert decide_module.strip_schedule("월/수요일 지정 배출") == ""
    assert decide_module.strip_schedule("월요일 배출. 헹군 후 펼쳐서 배출") == "헹군 후 펼쳐서 배출"
    assert decide_module.strip_schedule("라벨 제거 필수") == "라벨 제거 필수"


def test_district_info_never_contains_weekday_for_any_gu_and_category():
    import re

    data = decide_module.load_districts()
    codes = [c for c, cat in data["result_code_to_category_id"].items() if cat]
    for gu in data["gu_name_to_district_id"]:
        for code in codes:
            info = decide_module.district_info(gu, code)
            if info:
                assert not re.search(r"요일|매일|격일", info.prohibited_items + info.special_notes), (gu, code)


def test_haeundae_demo_district_has_no_schedule_leak():
    info = decide(obs("pet_clear_label"), REGION, None, 1).district_info
    assert info is not None and "요일" not in info.special_notes


COMPOSITE = "뚜껑·포장 비닐·라벨처럼 재질이 다른 부분이 붙어 있으면 떼어서 각각의 재질대로 분리배출하기"


def test_composite_note_for_mixed_material_any_product():
    # 물티슈뿐 아니라 AI가 여러 재질이 붙은 제품으로 본 항목이면 어떤 품목이든 분리 안내
    for name, extra in (("wet_tissue", {}), ("plastic_pp_clean", {"material_guess": "mixed"}), ("pet_clear_label", {"label_ko": "생수 6입 세트"})):
        d = decide(obs(name, **extra), REGION, None, 1)
        assert d.kind == "FINAL" and d.steps[-1] == COMPOSITE, name


def test_composite_note_absent_for_plain_and_split_items():
    assert COMPOSITE not in decide(obs("plastic_pp_clean"), REGION, None, 1).steps
    # AI가 포장 비닐을 따로 항목으로 쪼갠 경우(이름에 패키지·세트 없음) 중복 안내 없음
    assert COMPOSITE not in decide(obs("vinyl_clean", label_ko="포장 비닐"), REGION, None, 1).steps


# ---------- 코팅 종이 이유 표시, 캡 보정 ----------


def test_coated_paper_shows_reason_and_not_contradiction():
    soiled = {"level": "light", "type": "food", "likely_removable_by_rinsing": "unknown"}
    d = decide(obs("cardboard_tape", item_type="other", label_ko="코팅 종이 용기", coating_or_mixed_material="yes", contamination=soiled), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "GENERAL")
    assert "코팅된 종이 (종이류로 재활용되지 않아요)" in d.analysis_bullets and "음식물·기름 오염 있음" in d.analysis_bullets
    assert d.steps == ["코팅된 종이는 종이류로 재활용되지 않아요", "종량제 봉투에 넣어 배출하기"]
    assert d.source.url == "https://www.busan.go.kr/depart/ahwastepolicy09"


def test_coated_clean_paper_has_no_recyclable_line():
    d = decide(obs("cardboard_tape", item_type="other", coating_or_mixed_material="yes"), REGION, None, 1)
    assert d.result_code == "GENERAL"
    assert "오염 없음, 재활용 가능" not in d.analysis_bullets and "코팅된 종이 (종이류로 재활용되지 않아요)" in d.analysis_bullets


def test_food_soiled_paper_without_coating_unchanged():
    soiled = {"level": "light", "type": "oil", "likely_removable_by_rinsing": "unknown"}
    d = decide(obs("cardboard_tape", contamination=soiled), REGION, None, 1)
    assert d.result_code == "GENERAL" and "코팅된 종이 (종이류로 재활용되지 않아요)" not in d.analysis_bullets


def test_cap_read_as_small_plastic_goes_to_plastic():
    d = decide(obs("straw", label_ko="물티슈 캡", material_guess="PP"), REGION, None, 1)
    assert (d.kind, d.result_code) == ("FINAL", "PLASTIC")
    assert decide(obs("straw", label_ko="병뚜껑"), REGION, None, 1).result_code == "PLASTIC"


def test_real_straw_still_general():
    assert decide(obs("straw", label_ko="빨대"), REGION, None, 1).result_code == "GENERAL"
