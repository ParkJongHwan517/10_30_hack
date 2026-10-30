"""POST /api/decide — 담당: P. PROJECT_SPEC §10. AI를 호출하지 않는다(규칙만)."""

from fastapi import APIRouter

from ..models import Decision, DecideRequest
from ..services.decide import decide as run_rules

router = APIRouter()


@router.post("/decide", response_model=Decision)
def decide(req: DecideRequest) -> Decision:
    decision = run_rules(req.observation, req.region, req.answers, req.attempt)
    # TODO(P): Q의 services/log.py log_decision()이 들어오면 terminal 결과일 때 익명 로그 호출 (실패해도 무시)
    return decision
