"""POST /api/observe — 담당: 백엔드 1 (판독). PROJECT_SPEC §10."""

import os

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from ..models import ErrorResponse, Observation, ObserveResponse
from ..services import mock_vision, vision

router = APIRouter()

MAX_IMAGE_BYTES = 3 * 1024 * 1024  # §10: ≤ 3MB
MIN_CONFIDENCE = 0.6  # §9.1 공통 게이트 2


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content=ErrorResponse(code=code, message=message).model_dump())


def _gate(obs: Observation) -> tuple[bool, str | None]:
    """§9.1 공통 게이트 1·2 (3번 UNKNOWN은 decide 몫). 개인정보가 사진 품질보다 먼저."""
    if obs.privacy_flag:
        return False, "privacy"
    if obs.photo_quality != "good" or obs.confidence < MIN_CONFIDENCE:
        return False, "quality"
    return True, None


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
        obs = mock_vision.mock_observation(is_reshoot)
    else:
        try:
            obs = await run_in_threadpool(vision.observe, data, "image/jpeg")
        except vision.VisionBusy:
            return _error(503, "AI_BUSY", "잠시 후 다시 시도해주세요.")
        except vision.VisionFailed:
            return _error(502, "AI_UNAVAILABLE", "AI 응답을 받을 수 없습니다.")

    ok, reason = _gate(obs)
    return ObserveResponse(observation=obs, ok=ok, reason=reason, demo_mode=demo_mode)  # type: ignore[arg-type]
