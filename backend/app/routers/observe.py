"""POST /api/observe — 담당: 백엔드 1 (판독). PROJECT_SPEC §10."""

import os

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from ..models import ErrorResponse, Observation, ObserveResponse
from ..services import mock_vision, vision
from ..services.decide import photo_gate_reason

router = APIRouter()

MAX_IMAGE_BYTES = 3 * 1024 * 1024  # §10: ≤ 3MB

# 병·캔의 뚜껑은 본체와 함께 배출한다(부산시 안내: 투명 페트병은 "뚜껑 닫아 배출", 캔 뚜껑은 알루미늄).
# 프롬프트 규칙 7은 캡·뚜껑을 별도 항목으로 나누라고 해서(물티슈 캡·컵 뚜껑용) 병·캔 뚜껑까지 따로 나오므로 서버에서 거른다.
_BOTTLE_CAN_TYPES = {"pet_bottle", "can", "glass_bottle"}
_CAP_WORDS = ("뚜껑", "캡", "마개")
_PARENT_WORDS = ("캔", "병", "페트", "보틀")
_CAP_ITEM_TYPES = {"plastic_container", "small_plastic", "other"}


def drop_bottle_can_caps(items: list[Observation]) -> list[Observation]:
    """사진에 병·캔이 있으면, 이름이 '캔 뚜껑'·'페트병 뚜껑'처럼 병·캔의 뚜껑인 항목을 뺀다.

    '물티슈 캡'·'컵 뚜껑'처럼 병·캔 말이 없는 이름과, 병·캔 없이 뚜껑만 찍힌 사진은 그대로 둔다.
    """
    if not any(o.item_type in _BOTTLE_CAN_TYPES for o in items):
        return items

    def is_parent_cap(o: Observation) -> bool:
        label = o.label_ko or ""
        return (
            o.item_type in _CAP_ITEM_TYPES
            and any(w in label for w in _CAP_WORDS)
            and any(w in label for w in _PARENT_WORDS)
        )

    kept = [o for o in items if not is_parent_cap(o)]
    return kept or items


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content=ErrorResponse(code=code, message=message).model_dump())


@router.post("/observe", response_model=ObserveResponse)
async def observe(
    image: UploadFile = File(...),
    is_reshoot: bool = Form(False),
) -> ObserveResponse | JSONResponse:
    data = await image.read(MAX_IMAGE_BYTES + 1)  # 메모리에만 존재, 저장·로깅하지 않는다
    if not data:
        return _error(400, "NO_IMAGE", "이미지가 없습니다.")
    if len(data) > MAX_IMAGE_BYTES:
        return _error(413, "IMAGE_TOO_LARGE", "이미지 용량이 너무 큽니다.")
    if not data.startswith(b"\xff\xd8\xff"):  # JPEG 매직 바이트 (프론트가 JPEG로 재인코딩해서 보낸다)
        return _error(400, "BAD_IMAGE", "JPEG 이미지만 지원합니다.")

    demo_mode = os.getenv("MOCK_VISION", "").lower() == "true"
    if demo_mode:
        items = mock_vision.mock_items(is_reshoot)
    else:
        try:
            items = await run_in_threadpool(vision.observe, data, "image/jpeg")
        except vision.VisionBusy:
            return _error(503, "AI_BUSY", "잠시 후 다시 시도해주세요.")
        except vision.VisionFailed:
            return _error(502, "AI_UNAVAILABLE", "AI 응답을 받을 수 없습니다.")

    items = drop_bottle_can_caps(items)
    reason = photo_gate_reason(items)  # 사진 단위 게이트: 개인정보는 어느 항목이든, 품질은 대표 항목(items[0])만
    return ObserveResponse(observation=items[0], items=items, ok=reason is None, reason=reason, demo_mode=demo_mode)
