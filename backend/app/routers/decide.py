"""POST /api/decide — 담당: P. PROJECT_SPEC §10. AI를 호출하지 않는다(규칙만)."""

from fastapi import APIRouter

from ..models import Decision, DecideRequest
from ..services.decide import decide as run_rules
from ..services.log import log_decision

router = APIRouter()


@router.post("/decide", response_model=Decision)
def decide(req: DecideRequest) -> Decision:
    decision = run_rules(req.observation, req.region, req.answers, req.attempt)
    # 최종 결과(FINAL·UNKNOWN)만 익명 통계로 남긴다(§7.3). log_decision은 실패·타임아웃을 스스로 삼킨다.
    if decision.terminal:
        o = req.observation
        log_decision(
            gu=req.region.gu,
            item_type=o.item_type,
            kind=decision.kind,
            result_code=decision.result_code,
            attempt=req.attempt,
            photo_quality=o.photo_quality,
            privacy_flag=o.privacy_flag,
            rules_verified=decision.rules_verified,
            demo_mode=req.demo_mode,
        )
    return decision
