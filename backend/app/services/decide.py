"""규칙 엔진 (PROJECT_SPEC §9). 담당: P.

순수 함수로 유지한다: AI·네트워크를 호출하지 않는다. 배출 판단은 여기와 rules.busan.json에서만 나온다.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from ..models import Answers, Decision, DistrictInfo, Observation, Question, Region, ResultCode, Source
from .bullets import build_bullets, is_box_like

RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "rules.busan.json"
CONFIDENCE_THRESHOLD = 0.6
FOOD_TYPES = {"food", "sauce", "oil"}

# 보완 화면 문구 (§5.2). 규칙 데이터가 아니라 화면 고정 문구라 코드에 둔다.
RESHOOT_HEADLINE = "사진이 불명확해요."
UNKNOWN_HEADLINE = "정확히 판단하기 어려워요."


@lru_cache
def load_rules() -> dict[str, Any]:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def lookup_rule(code: ResultCode) -> dict[str, Any]:
    return load_rules()["results"][code]


def gate_reason(o: Observation) -> Literal["privacy", "quality"] | None:
    """§9.1 공통 게이트 1·2. /api/observe의 ok/reason 판정도 이 함수를 쓴다(기준을 한 곳에 둔다).

    개인정보가 사진 품질보다 먼저다. 통과하면 None.
    """
    if o.privacy_flag:
        return "privacy"
    if o.photo_quality != "good" or o.confidence < CONFIDENCE_THRESHOLD:
        return "quality"
    return None


def photo_gate_reason(items: list[Observation]) -> Literal["privacy", "quality"] | None:
    """사진 전체를 다시 찍게 할지 (/api/observe의 ok/reason, 여러 항목용).

    개인정보는 어느 항목에서든 보이면 전체 재촬영. 품질은 대표 항목(items[0], 가장 큰 것)만 본다 —
    빨대처럼 작은 구성품은 신뢰도가 낮게 나오기 쉬워서, 그 때문에 사진 전체를 막지 않는다.
    작은 항목의 저품질은 항목별 /api/decide가 그 항목만 RESHOOT_QUALITY로 돌려준다.
    """
    if not items:
        return "quality"
    if any(o.privacy_flag for o in items):
        return "privacy"
    return gate_reason(items[0])


def needs_question(o: Observation, answer: str | None, attempt: int) -> bool:
    return o.contamination.level != "none" and attempt == 1 and answer is None


class _Ctx:
    """basis_label·출처처럼 모든 Decision에 공통으로 들어가는 값."""

    def __init__(self) -> None:
        rules = load_rules()
        self.verified: bool = rules["busan_verified"]
        self.basis_label: str = rules["basis_label_verified" if self.verified else "basis_label_unverified"]

    def source(self, code: ResultCode = "GENERAL") -> Source:
        rule = lookup_rule(code)
        # 검증되지 않은 URL은 근거 링크로 걸지 않는다 (§13-2)
        return Source(label=rule["source_label"], url=rule["source_url"] if self.verified else None)

    def final(self, code: ResultCode, bullets: list[str], override: dict[str, Any] | None = None) -> Decision:
        """override: 같은 결과 코드라도 근거·배출 방법이 다른 경우(예: 작은 플라스틱 → 환경부 근거)."""
        rule = {**lookup_rule(code), **(override or {})}
        return Decision(
            kind="FINAL",
            result_code=code,
            basis_label=self.basis_label,
            headline=rule["headline"],
            analysis_bullets=bullets,
            steps=rule["steps"],
            source=Source(label=rule["source_label"], url=rule["source_url"] if self.verified else None),
            rules_verified=self.verified,
            terminal=True,
        )

    def non_final(self, kind, headline: str, terminal: bool, **kw) -> Decision:
        return Decision(
            kind=kind,
            basis_label=self.basis_label,
            headline=headline,
            source=self.source(),
            rules_verified=self.verified,
            terminal=terminal,
            **kw,
        )


def _washable(
    ctx: _Ctx, o: Observation, answer: str | None, attempt: int, clean_code: ResultCode
) -> Decision:
    """스티로폼·플라스틱 용기 공통: 오염 → 질문 → 세척·재촬영 / 일반폐기물 (§9.1)."""
    if o.contamination.level == "none":
        return ctx.final(clean_code, build_bullets(o, washed=attempt == 2))
    if attempt == 2:
        return ctx.final("GENERAL", build_bullets(o, extra="세척 후에도 오염이 남아 있음"))
    if needs_question(o, answer, attempt):
        q = load_rules()["question"]
        return ctx.non_final("ASK_QUESTION", q["text"], False, question=Question.model_validate(q))
    if answer == "yes":
        g = load_rules()["wash_guide"]
        return ctx.non_final("WASH_AND_RESHOOT", g["headline"], False, wash_checklist=g["checklist"])
    # "잘 모르겠어요"는 "아니요"와 같게 처리한다(보수적)
    return ctx.final("GENERAL", build_bullets(o, extra="오염 제거 어려움 (사용자 답변)"))


def _decide(
    observation: Observation,
    region: Region | dict,
    answers: Answers | dict | None,
    attempt: int,
) -> Decision:
    """region은 MVP에서 판단에 쓰지 않는다(부산 공통 1벌, gu는 표시·로그용)."""
    o = observation
    answer = Answers.model_validate(answers).contamination_removable if answers else None
    ctx = _Ctx()

    if reason := gate_reason(o):
        return ctx.non_final("RESHOOT_QUALITY", RESHOOT_HEADLINE, False, reshoot_reason=reason)

    match o.item_type:
        case "pet_bottle":
            code: ResultCode = "PET_CLEAR" if o.is_transparent_colorless == "yes" else "PLASTIC"
            return ctx.final(code, build_bullets(o))
        case "styrofoam_container":
            if o.is_white == "no" or o.coating_or_mixed_material == "yes":
                return ctx.final("GENERAL", build_bullets(o))
            return _washable(ctx, o, answer, attempt, "STYROFOAM")
        case "plastic_container":
            if o.coating_or_mixed_material == "yes":
                return ctx.final("GENERAL", build_bullets(o))
            return _washable(ctx, o, answer, attempt, "PLASTIC")
        case "cardboard_box":
            return _paper(ctx, o)
        case "can":
            # 부산시 안내: 이물질 제거 후 캔류로 배출. 내용물·오염은 헹구면 되므로 질문 없이 배출 방법으로 안내한다
            return ctx.final("CAN", build_bullets(o))
        case "vinyl":
            # 부산시 안내: 이물질 묻은 비닐은 종량제. 비닐은 세척·재촬영 대신 바로 안내한다
            if o.contamination.level != "none":
                return ctx.final("GENERAL", build_bullets(o))
            return ctx.final("VINYL", build_bullets(o))
        case "glass_bottle":
            # 부산시 안내: 깨진 유리병은 불연성 쓰레기
            if o.damage == "broken":
                return ctx.final("NONCOMBUSTIBLE", build_bullets(o))
            return ctx.final("GLASS", build_bullets(o))
        case "small_plastic":
            # 부산시 안내엔 없음 → 환경부 공통 가이드라인: 작은 플라스틱은 선별이 안 돼 종량제
            return ctx.final("GENERAL", build_bullets(o), override=load_rules()["small_plastic"])
        case "wet_tissue":
            return ctx.final("GENERAL", build_bullets(o), override=load_rules()["wet_tissue"])
        case "general_waste":
            return ctx.final("GENERAL", build_bullets(o), override=load_rules()["general_waste"])
        case "noncombustible_item":
            return ctx.final("NONCOMBUSTIBLE", build_bullets(o), override=load_rules()["noncombustible_item"])
        case "paper_pack":
            # 부산시 종이류 안내: 종이팩은 종이류와 구분해 따로 배출
            return ctx.final("PAPER_PACK", build_bullets(o))
        case "receipt_coated_paper":
            # 부산시 종이류 안내: 영수증·전표·코팅지는 종이류로 배출하면 안 되는 품목(종량제)
            return ctx.final("GENERAL", build_bullets(o), override=load_rules()["receipt_coated_paper"])
        case "other" if o.material_guess == "paper":
            # AI가 과자 상자·종이 용기를 상자로 못 보고 other로 내도 재질이 종이면 종이 규칙을 적용한다
            return _paper(ctx, o)

    return ctx.non_final("UNKNOWN", UNKNOWN_HEADLINE, True)


def _paper(ctx: _Ctx, o: Observation) -> Decision:
    """음식물·기름 오염 또는 코팅이면 종량제, 아니면 종이류 (부산시 종이류 안내)."""
    food_soiled = o.contamination.level != "none" and o.contamination.type in FOOD_TYPES
    if food_soiled or o.coating_or_mixed_material == "yes":
        return ctx.final("GENERAL", build_bullets(o))
    if not is_box_like(o):
        # 컵홀더·종이 용기처럼 상자가 아닌 종이는 "상자를 펼쳐" 대신 일반 종이류 문구(AI가 cardboard_box로 내도 적용)
        return ctx.final("PAPER", build_bullets(o), override=load_rules()["paper_other"])
    return ctx.final("PAPER", build_bullets(o))


DISTRICTS_PATH = RULES_PATH.with_name("rules.busan.districts.json")
UNVERIFIED_LABEL = "{gu} 안내 (팀 조사 기준, 공식 링크 없음 — 구청 안내를 확인하세요)"


@lru_cache
def load_districts() -> dict[str, Any]:
    return json.loads(DISTRICTS_PATH.read_text(encoding="utf-8"))


def district_info(gu: str, code: ResultCode | None) -> DistrictInfo | None:
    """판정한 결과 코드 → 구 데이터 분류로 연결. 일반폐기물(GENERAL)·위험물 등 대응 분류가 없으면 None.

    요일·배출 방법(disposal_method)은 구가 아니라 동·권역별로 달라 내려주지 않는다.
    """
    data = load_districts()
    category = data["result_code_to_category_id"].get(code) if code else None
    district_id = data["gu_name_to_district_id"].get(gu)
    rule = data["districts"].get(district_id, {}).get("rules", {}).get(category) if category and district_id else None
    if not rule:
        return None
    link = data.get("verified_districts", {}).get(district_id)
    return DistrictInfo(
        gu=gu,
        prohibited_items=rule.get("prohibited_items", ""),
        special_notes=rule.get("special_notes", ""),
        verified=bool(link),
        source_label=f"{gu} 안내 (공식 확인)" if link else UNVERIFIED_LABEL.format(gu=gu),
        source_url=link or None,
    )


def decide(
    observation: Observation,
    region: Region | dict,
    answers: Answers | dict | None,
    attempt: int,
) -> Decision:
    """규칙 판단(_decide) 결과에 구 안내를 붙인다. 구 안내는 최종 결과(FINAL)에만, 부산시 규칙 판단은 바꾸지 않는다."""
    decision = _decide(observation, region, answers, attempt)
    if decision.kind == "FINAL":
        gu = region["gu"] if isinstance(region, dict) else region.gu
        decision.district_info = district_info(gu, decision.result_code)
    return decision
