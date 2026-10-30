"""POST /api/decide — 담당: 백엔드 2 (규칙·데이터). PROJECT_SPEC §10."""

from fastapi import APIRouter, HTTPException

from ..models import Decision, DecideRequest

router = APIRouter()


@router.post("/decide", response_model=Decision)
def decide(req: DecideRequest) -> Decision:
    # TODO(백엔드2): services/decide.py decide() 호출 → (선택) services/log.py 익명 로그
    raise HTTPException(status_code=501, detail="not implemented")
