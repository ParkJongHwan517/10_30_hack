"""POST /api/observe — 담당: 백엔드 1 (판독). PROJECT_SPEC §10."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..models import ObserveResponse

router = APIRouter()


@router.post("/observe", response_model=ObserveResponse)
async def observe(
    image: UploadFile = File(...),
    is_reshoot: bool = Form(False),
) -> ObserveResponse:
    # TODO(백엔드1): MOCK_VISION 분기 → services/vision.py observe() → 공통 게이트 판정(§9.1 1·2)
    raise HTTPException(status_code=501, detail="not implemented")
