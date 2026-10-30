"""MOCK_VISION=true 일 때 Gemini 대신 돌려주는 고정 관찰값. PROJECT_SPEC §11 골든 아웃풋 기준.

TODO(jonghwan): D의 backend/tests 픽스처가 main에 들어오면 같은 값을 재사용하도록 맞춘다.
"""

import os

from ..models import Attachments, Contamination, Observation


def _attach(label: str = "no", tape: str = "no", waybill: str = "no", lid: str = "no") -> Attachments:
    return Attachments(label_present=label, tape_present=tape, waybill_present=waybill, lid_present=lid)  # type: ignore[arg-type]


_NO_CONTAMINATION = Contamination(level="none", type="none", likely_removable_by_rinsing="unknown")

# 이름은 §11 골든 ID. MOCK_FIXTURE 환경변수로 고른다(기본 G1).
_FIXTURES: dict[str, Observation] = {
    "G1": Observation(
        item_type="pet_bottle", material_guess="PET", is_transparent_colorless="yes", is_white="unknown",
        contents_present="no", contamination=_NO_CONTAMINATION, attachments=_attach(label="yes"),
        damage="none", coating_or_mixed_material="no", privacy_flag=False, photo_quality="good",
        confidence=0.95, notes_ko="라벨이 붙은 투명 페트병이며 내용물은 보이지 않습니다.",
    ),
    "G2": Observation(
        item_type="styrofoam_container", material_guess="EPS", is_transparent_colorless="unknown", is_white="yes",
        contents_present="yes", contamination=Contamination(level="heavy", type="sauce", likely_removable_by_rinsing="unknown"),
        attachments=_attach(), damage="none", coating_or_mixed_material="no", privacy_flag=False,
        photo_quality="good", confidence=0.9, notes_ko="소스가 묻은 흰색 스티로폼 용기입니다.",
    ),
    "G5": Observation(
        item_type="styrofoam_container", material_guess="EPS", is_transparent_colorless="unknown", is_white="yes",
        contents_present="no", contamination=_NO_CONTAMINATION, attachments=_attach(),
        damage="none", coating_or_mixed_material="no", privacy_flag=False, photo_quality="good",
        confidence=0.92, notes_ko="오염이 없는 깨끗한 흰색 스티로폼 용기입니다.",
    ),
    "G6": Observation(
        item_type="plastic_container", material_guess="PP", is_transparent_colorless="unknown", is_white="unknown",
        contents_present="no", contamination=_NO_CONTAMINATION, attachments=_attach(),
        damage="none", coating_or_mixed_material="no", privacy_flag=False, photo_quality="good",
        confidence=0.9, notes_ko="깨끗한 플라스틱 배달 용기(PP 추정)입니다.",
    ),
    "G7": Observation(
        item_type="cardboard_box", material_guess="paper", is_transparent_colorless="unknown", is_white="unknown",
        contents_present="no", contamination=_NO_CONTAMINATION, attachments=_attach(tape="yes"),
        damage="none", coating_or_mixed_material="no", privacy_flag=False, photo_quality="good",
        confidence=0.9, notes_ko="테이프가 붙은 골판지 택배 상자입니다.",
    ),
    # 공통 게이트 확인용 (§9.1 1~3)
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


def mock_observation(is_reshoot: bool = False) -> Observation:
    """MOCK_FIXTURE(기본 G1)에 해당하는 관찰값. G2 재촬영(is_reshoot)이면 세척 후인 G5를 돌려준다(경로 A 시연용)."""
    name = os.getenv("MOCK_FIXTURE", "G1").upper()
    if name == "G2" and is_reshoot:
        name = "G5"
    return _FIXTURES.get(name, _FIXTURES["G1"]).model_copy(deep=True)
