"""MOCK_VISION=true 일 때 Gemini 대신 돌려주는 고정 관찰값. PROJECT_SPEC §11 골든 아웃풋 기준.

골든(G1·G2·G5·G6·G7)과 복합 쓰레기(COFFEE)는 D의 backend/tests/fixtures/*.json을 그대로 재사용한다(§11). 값은 여기서 복제하지 않는다.
Vercel 번들에 포함되도록 vercel.json의 includeFiles에 해당 경로를 넣어 두었다.
"""

import os
from pathlib import Path

from pydantic import TypeAdapter

from ..models import Attachments, Contamination, Observation

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
_GOLDEN_FILES = {
    "G1": "pet_clear_label",
    "G2": "styrofoam_sauce",
    "G5": "styrofoam_clean",  # G2 경로 A 재촬영 후
    "G6": "plastic_pp_clean",
    "G7": "cardboard_tape",
}
_MULTI_FILES = {"COFFEE": "multi_coffee_cup"}  # 목록 픽스처: 컵 본체·뚜껑·컵홀더·빨대
_ITEMS = TypeAdapter(list[Observation])


def _load(name: str) -> Observation:
    return Observation.model_validate_json((_FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _attach(label: str = "no", tape: str = "no", waybill: str = "no", lid: str = "no") -> Attachments:
    return Attachments(label_present=label, tape_present=tape, waybill_present=waybill, lid_present=lid)  # type: ignore[arg-type]


_NO_CONTAMINATION = Contamination(level="none", type="none", likely_removable_by_rinsing="unknown")

# 공통 게이트 확인용 합성값. MOCK_FIXTURE 환경변수로 고른다.
_GATE_FIXTURES: dict[str, Observation] = {
    # §9.1 1~3
    "BLURRY": Observation(
        item_type="unknown", material_guess="unknown", is_transparent_colorless="unknown", is_white="unknown",
        contents_present="unknown", contamination=Contamination(level="unknown", type="unknown", likely_removable_by_rinsing="unknown"),
        attachments=_attach("unknown", "unknown", "unknown", "unknown"), damage="unknown",
        coating_or_mixed_material="unknown", privacy_flag=False, photo_quality="blurry",
        confidence=0.3, notes_ko="사진이 흐려 대상을 확인하기 어렵습니다.",
    ),
    "PRIVACY": Observation(
        item_type="cardboard_box", material_guess="paper", is_transparent_colorless="unknown", is_white="unknown",
        contents_present="no", contamination=_NO_CONTAMINATION, attachments=_attach(waybill="yes"),
        damage="none", coating_or_mixed_material="unknown", privacy_flag=True, photo_quality="good",
        confidence=0.9, notes_ko="택배 상자에 송장이 보입니다.",
    ),
    "UNKNOWN": Observation(
        item_type="unknown", material_guess="unknown", is_transparent_colorless="unknown", is_white="unknown",
        contents_present="unknown", contamination=Contamination(level="unknown", type="unknown", likely_removable_by_rinsing="unknown"),
        attachments=_attach("unknown", "unknown", "unknown", "unknown"), damage="unknown",
        coating_or_mixed_material="unknown", privacy_flag=False, photo_quality="good",
        confidence=0.8, notes_ko="어떤 물체인지 판별하기 어렵습니다.",
    ),
}


def mock_items(is_reshoot: bool = False) -> list[Observation]:
    """MOCK_FIXTURE(기본 G1)에 해당하는 항목 목록. 단일 품목은 길이 1짜리 목록으로 돌려준다.

    COFFEE면 복합 쓰레기(4개 항목). G2 재촬영(is_reshoot)이면 세척 후인 G5를 돌려준다(경로 A 시연용).
    """
    name = os.getenv("MOCK_FIXTURE", "G1").upper()
    if name in _MULTI_FILES:
        return _ITEMS.validate_json((_FIXTURE_DIR / f"{_MULTI_FILES[name]}.json").read_text(encoding="utf-8"))
    if name == "G2" and is_reshoot:
        name = "G5"
    if name in _GATE_FIXTURES:
        return [_GATE_FIXTURES[name].model_copy(deep=True)]
    return [_load(_GOLDEN_FILES.get(name, _GOLDEN_FILES["G1"]))]
