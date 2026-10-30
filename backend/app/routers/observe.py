"""POST /api/observe — 담당: 백엔드 1 (판독). PROJECT_SPEC §10."""

import os

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from ..models import ErrorResponse, ObserveResponse
from ..services import mock_vision, vision
from ..services.decide import photo_gate_reason

router = APIRouter()

MAX_IMAGE_BYTES = 3 * 1024 * 1024  # §10: ≤ 3MB


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

    reason = photo_gate_reason(items)  # 사진 단위 게이트: 개인정보는 어느 항목이든, 품질은 대표 항목(items[0])만
    return ObserveResponse(observation=items[0], items=items, ok=reason is None, reason=reason, demo_mode=demo_mode)
