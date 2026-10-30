# 여러 물건 동시 판독 (v2) 설계 — 2026-10-30 P

> 상태: **제안 (팀 합의 전)**. 합의되면 P가 `models.py`부터 올린다.
> 목표: 사진 1장에 물건이 여러 개(예: 커피컵 = 컵·뚜껑·빨대·홀더)여도 **다시 찍게 하지 않고, 물건별 결과를 한 화면에** 보여준다.

## 1. 사용자 흐름

```
사진 1장 → /api/v2/observe : AI가 물건별로 나눠 관찰 (큰 것부터 최대 4개)
         → /api/v2/decide  : 물건마다 규칙 판단
         → 결과 화면: 물건별 카드
              · 바로 판단되는 물건  → 결과 카드
              · 오염돼 질문이 필요한 물건 → 질문을 한 화면에 모아서 1번만
              · 세척이 필요한 물건 → 그 카드에 "이것만 씻어서 다시 찍기"
```

- **다시 찍기 요청은 사진 전체가 흐리거나 개인정보가 보일 때만.** 물건이 여러 개라는 이유로 막지 않는다.
- 세척 후 재촬영은 **그 물건 하나만** 다시 찍고, 그 카드만 교체한다. 나머지 카드는 유지.
- 지원 품목이 아닌 물건은 그 카드만 "정확히 판단하기 어려워요". 전체를 막지 않는다.

## 2. API (v2, 기존 v1은 그대로 둔다)

전환 중에도 데모가 깨지지 않게 **새 엔드포인트로 추가**한다. 프론트가 v2로 옮기면 v1은 나중에 정리.

```python
# models.py (P)
class ItemObservation(BaseModel):          # 기존 Observation에서 사진 단위 필드를 뺀 것
    label_ko: str                          # 카드 제목용 짧은 이름 (예: "컵 뚜껑"). 브랜드 금지
    item_type, material_guess, is_transparent_colorless, is_white, contents_present,
    contamination, attachments, damage, coating_or_mixed_material, confidence, notes_ko

class PhotoObservation(BaseModel):         # Gemini response_schema
    items: list[ItemObservation]           # 1~4개, 큰 것부터
    privacy_flag: bool                     # 사진 단위
    photo_quality: Literal["good", "blurry", "dark", "partial"]

class ObserveResponseV2(BaseModel):
    observation: PhotoObservation
    ok: bool
    reason: Literal["quality", "privacy"] | None
    demo_mode: bool

class DecideRequestV2(BaseModel):
    region: Region
    observation: PhotoObservation
    answers: dict[int, Tri] = {}           # 물건 번호 → "이물질을 제거할 수 있나요?" 답
    attempt: Literal[1, 2] = 1             # 2 = 세척 후 재촬영(그 물건만 찍은 사진)
    demo_mode: bool = False

class ItemDecision(BaseModel):             # 기존 Decision과 같은 필드 + 번호·이름
    index: int
    label_ko: str
    kind: Literal["ASK_QUESTION", "WASH_AND_RESHOOT", "FINAL", "UNKNOWN"]
    result_code, headline, analysis_bullets, steps, question, wash_checklist

class DecideResponseV2(BaseModel):
    kind: Literal["RESULTS", "RESHOOT_QUALITY"]   # 사진 단위
    reshoot_reason: Literal["quality", "privacy"] | None
    items: list[ItemDecision]
    basis_label: str
    source: Source
    rules_verified: bool
```

- 프론트는 `items` 중 `ASK_QUESTION`이 있으면 질문 화면(모아서), 없으면 결과 화면.
- 답을 받으면 같은 `observation` + `answers`로 다시 `/api/v2/decide`.
- 익명 로그는 **최종 판단된 물건마다 1행** (테이블 변경 없음).

## 3. 역할별 할 일

### P (준호) — 먼저 (프론트·Q가 이걸 기다림)
1. `models.py`에 위 v2 모델 추가 → `api-types.ts` 재생성
2. `services/decide.py`에 `decide_v2()` — 물건마다 기존 `decide` 규칙 재사용, 사진 단위 게이트(`gate_reason`)
3. 작은 플라스틱(빨대 등) 규칙 — 부산시 근거 확인 후 추가 (근거 없으면 UNKNOWN 유지)
4. `routers/decide.py`에 `POST /api/v2/decide`, 물건별 로그
5. 픽스처: 커피컵 4부품, 도시락(용기+뚜껑+나무젓가락) → 테스트·스모크
6. 스펙 §12 촬영 안내 문구 수정: "쓰레기 하나만 크게" → "쓰레기가 잘 보이게"

### Q (종환)
1. `vision.py`에 `observe_v2()` — `response_schema=PhotoObservation`
2. 프롬프트(§8.1) 1번 규칙 수정 (P 승인):
   "사진에 보이는 쓰레기를 물건별로 나눠 큰 것부터 최대 4개 보고하세요. 붙어 있어도 따로 버리는 부품(뚜껑·빨대·컵홀더·라벨)은 각각 보고하세요. label_ko에 브랜드 없이 짧은 이름을 쓰세요."
3. `POST /api/v2/observe` (`routers/observe.py`), 게이트는 `gate_reason`을 사진 단위로
4. `mock_vision.py`에 v2 데모 응답 (P의 커피컵 픽스처 재사용)
5. **응답 시간** — 커피컵 4부품 9초 → 목표 6초 이하 (thinking LOW 유지, 최대 4개 제한, notes_ko 짧게)

### 프론트 리드
1. v2 API로 전환 (`lib/api.ts`)
2. 결과 화면: 물건별 카드 목록 (`label_ko` 제목, 결과 색은 `result_code`별 — `GENERAL`·`NONCOMBUSTIBLE` 빨강, 나머지 초록)
3. 질문 화면: 질문이 필요한 물건들을 한 화면에 (물건마다 3지선다)
4. 세척 카드: "이것만 씻어서 다시 찍기" → 재촬영 → 그 카드만 교체
5. 촬영 안내 문구를 스펙 §12 새 문구로

## 4. 일정 (KST)

| 시각 | 할 일 |
|---|---|
| ~19:00 | P: v2 모델·규칙·데모 픽스처 main 머지 → 프론트는 데모 모드로 화면 작업 시작 |
| ~20:00 | Q: `observe_v2`·`/api/v2/observe` main 머지 |
| ~22:30 | 프론트: v2 화면 완성 |
| ~23:30 | 실제 사진으로 모델·프롬프트 최종 조정, 시연 사진 확정 |
| 01:00 | 기능 동결 (안 끝나면 v1로 시연) |
