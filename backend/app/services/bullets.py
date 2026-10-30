"""결과 화면 "AI 분석 결과" 불릿 생성 (PROJECT_SPEC §9.4). 담당: P.

줄 순서는 디자인 이미지 ④를 따른다: 병·캔·종이류는 부착물이 오염보다 먼저, 용기·비닐은 오염이 먼저.
"""

from ..models import Observation

MAX_BULLETS = 4
BOTTLE_LIKE = ("pet_bottle", "can", "glass_bottle")  # 오염 대신 내용물 유무를 보여준다


def _is_paper(o: Observation) -> bool:
    # decide와 같은 기준: AI가 other로 냈어도 재질이 종이면 종이로 다룬다
    return o.item_type == "cardboard_box" or (o.item_type == "other" and o.material_guess == "paper")


def _item_line(o: Observation) -> str | None:
    match o.item_type:
        case "pet_bottle":
            return "페트병 (투명)" if o.is_transparent_colorless == "yes" else "페트병 (유색)"
        case "styrofoam_container":
            return "스티로폼 용기"
        case "plastic_container":
            return "플라스틱 배달 용기(PP 추정)" if o.material_guess == "PP" else "플라스틱 배달 용기"
        case "cardboard_box":
            return "종이상자"
        case "can":
            return "캔 (금속)"
        case "vinyl":
            return "비닐류"
        case "glass_bottle":
            return "유리병"
        case "small_plastic":
            return "작은 플라스틱 (빨대·일회용 수저 등)"
        case "other" if o.material_guess == "paper":
            return "종이류"
    return None


def _contamination_line(o: Observation, washed: bool) -> str | None:
    if o.item_type in BOTTLE_LIKE:
        return "내용물 있음" if o.contents_present == "yes" else "내용물 없음"
    clean = o.contamination.level == "none"
    if _is_paper(o):
        return "오염 없음, 재활용 가능" if clean else "음식물·기름 오염 있음"
    if o.item_type == "vinyl":
        return "이물질 없음" if clean else "이물질 묻음"
    if clean:
        return "음식물·소스 오염 없음 (세척 완료)" if washed else "오염 없음 (깨끗함)"
    return "음식물·소스 오염 있음"


def _attachment_lines(o: Observation) -> list[str]:
    lines = []
    if o.attachments.label_present == "yes":
        lines.append("라벨 부착 있음")
    if o.attachments.tape_present == "yes":
        lines.append("테이프 부착 있음")
    if not lines and o.item_type == "plastic_container":
        lines.append("라벨·부착물 없음")
    return lines


def build_bullets(o: Observation, *, washed: bool = False, extra: str | None = None) -> list[str]:
    """extra: 판단 사유 줄(예: "오염 제거 어려움 (사용자 답변)"). 있으면 파손 줄 대신 넣는다(이미지 ④-2 기준)."""
    item = _item_line(o)
    contamination = _contamination_line(o, washed)
    attachments = _attachment_lines(o)

    if o.item_type in BOTTLE_LIKE or _is_paper(o):
        lines = [item, *attachments, contamination]
    else:
        lines = [item, contamination, *attachments]

    if extra:
        lines.append(extra)
    elif o.item_type == "glass_bottle" and o.damage == "broken":
        lines.append("깨짐 있음")
    elif o.damage == "none" and not _is_paper(o) and o.item_type not in ("vinyl", "small_plastic"):
        lines.append("파손 없음")

    return [line for line in lines if line][:MAX_BULLETS]
