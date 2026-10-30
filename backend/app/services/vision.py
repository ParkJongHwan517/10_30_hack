"""Gemini 비전 호출. Gemini는 이 파일에서만 호출한다(CLAUDE.md §6). PROJECT_SPEC §8.

AI는 관찰만 한다 — 배출 방법 판단은 규칙 엔진(decide)이 한다.
이미지 바이트는 메모리에서만 쓰고 로그·파일로 남기지 않는다.
"""

import os
import time
from typing import Any

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from ..models import Attachments, Contamination, Observation

DEFAULT_MODEL = "gemini-3.5-flash"
TIMEOUT_MS = 20_000  # §8.2 타임아웃 20초
RETRY_DELAY_S = 1.0

# §8.1 그대로 사용 (수정은 A 승인)
SYSTEM_PROMPT = """당신은 "분리배출 사진 관찰기"입니다.
사진에 보이는 쓰레기 하나에 대해 종류, 재질, 오염 및 부착물 상태를 관찰해 JSON으로만 보고합니다.

규칙:
1. 어떻게 버려야 하는지(배출 방법·분류)는 절대 판단하거나 언급하지 마세요. 그것은 다른 시스템이 합니다.
2. 사진에서 확인되지 않는 것은 추측하지 말고 "unknown"으로 표기하세요.
3. 사진이 흐리거나 어둡거나 대상이 일부만 보이면 photo_quality에 반영하고 confidence를 낮추세요.
4. 사람의 얼굴, 택배 송장의 이름·주소·전화번호 등 개인정보가 보이면 privacy_flag를 true로 하세요. 그 내용을 출력에 옮겨 적지 마세요.
5. 제품의 브랜드명·상표는 기록하지 마세요.
6. 출력은 지정된 스키마의 JSON 객체 하나뿐입니다. 설명 문장, 마크다운, 코드블록을 붙이지 마세요."""

USER_PROMPT = "이 사진의 쓰레기를 관찰해 JSON으로 보고하세요."


class VisionBusy(Exception):
    """쿼터 초과(429)·타임아웃 → 503 AI_BUSY."""


class VisionFailed(Exception):
    """키 누락·인증/요청 오류 등 AI 응답을 받을 수 없음 → 502."""


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise VisionFailed("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=TIMEOUT_MS))
    return _client


def _thinking(model: str) -> types.ThinkingConfig | None:
    """20초 타임아웃 안에 들어오도록 thinking을 최소화한다. 모델 세대마다 파라미터가 다르다."""
    if "gemini-3" in model:
        return types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)
    if "2.5-flash" in model:
        return types.ThinkingConfig(thinking_budget=0)
    return None


def _config(model: str) -> types.GenerateContentConfig:
    thinking = _thinking(model)
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=Observation,
        temperature=0,
        thinking_config=thinking,
    )


def _is_busy(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException | TimeoutError):
        return True
    return isinstance(exc, errors.APIError) and exc.code in (429, 503, 504)


def _fallback() -> Observation:
    """검증 실패가 반복될 때: '다시 촬영' 경로로 보낸다(§8.2)."""
    unk: Any = "unknown"
    return Observation(
        item_type=unk, material_guess=unk, is_transparent_colorless=unk, is_white=unk, contents_present=unk,
        contamination=Contamination(level=unk, type=unk, likely_removable_by_rinsing=unk),
        attachments=Attachments(label_present=unk, tape_present=unk, waybill_present=unk, lid_present=unk),
        damage=unk, coating_or_mixed_material=unk, privacy_flag=False, photo_quality="partial",
        confidence=0.0, notes_ko="사진을 정확히 관찰하지 못했습니다.",
    )


def _call(image_bytes: bytes, mime_type: str) -> Observation | None:
    """Gemini 1회 호출. 응답이 스키마에 맞지 않으면 None."""
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    resp = _get_client().models.generate_content(
        model=model,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), USER_PROMPT],
        config=_config(model),
    )
    parsed = resp.parsed
    if isinstance(parsed, Observation):
        return parsed
    try:
        return Observation.model_validate_json(resp.text or "")
    except (ValidationError, ValueError):
        return None


def observe(image_bytes: bytes, mime_type: str = "image/jpeg") -> Observation:
    """사진 1장 → Observation. 429·타임아웃은 1회 재시도 후 VisionBusy, 스키마 불일치는 1회 재시도 후 대체값."""
    for attempt in (1, 2):
        try:
            obs = _call(image_bytes, mime_type)
        except VisionFailed:
            raise
        except Exception as exc:  # noqa: BLE001 — SDK/네트워크 예외를 분류해 처리
            if _is_busy(exc):
                if attempt == 2:
                    raise VisionBusy(str(type(exc).__name__)) from exc
                time.sleep(RETRY_DELAY_S)
                continue
            raise VisionFailed(str(type(exc).__name__)) from exc
        if obs is not None:
            obs.confidence = min(1.0, max(0.0, obs.confidence))  # 서버에서 0~1로 clamp
            return obs
    return _fallback()
