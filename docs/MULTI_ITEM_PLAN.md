# 여러 항목(복합 쓰레기) 판독 — 2026-10-30 합의안

> Q의 [복합 쓰레기 분리 기능 — 진행 확인 요청] 기준. **기존 API(`/api/observe`, `/api/decide`)를 유지하고 목록만 붙인다.**
> 순서: ① P 계약 머지 → ② Q·프론트 작업 시작.

## 흐름

```
사진 1장 → /api/observe : AI가 항목(따로 버리는 물건·구성품)별로 관찰, 큰 것부터 최대 6개
         → 프론트가 항목마다 /api/decide 호출 → 항목별 결과 카드
```

- 사진 전체 재촬영은 **개인정보(어느 항목이든)** 또는 **대표 항목(items[0]) 품질**일 때만.
- 작은 항목(빨대 등)의 신뢰도가 낮으면 그 항목의 `/api/decide`만 `RESHOOT_QUALITY` → 프론트는 그 카드만 "따로 찍어 확인해 주세요".
- 지원 안 되는 항목은 그 카드만 `UNKNOWN`. 전체를 막지 않는다.

## 계약 (P, 이번 PR)

| 변경 | 내용 |
|---|---|
| `ObserveResponse.items?: Observation[]` | 항목 목록. `observation`은 `items[0]`(하위 호환). api-types에서 선택 필드라 기존 프론트 코드 안 깨짐 |
| `Observation.label_ko: str` (기본 `""`) | 카드 제목용 짧은 이름 ("컵 뚜껑"). 브랜드 금지 |
| `item_type: "small_plastic"` | 빨대·일회용 숟가락·포크 → 일반폐기물. 근거: 서울시 안내(2021.12.10, 부산시 안내엔 없음), 결과의 `source`도 서울시 글로 표시 |
| `services.decide.photo_gate_reason(items)` | 사진 단위 게이트. Q는 `observe.py`에서 이걸 호출 |
| 종이 보완 (PR #17) | `item_type=other` + `material_guess=paper` → 종이 규칙 (컵홀더 → 종이류) |

`/api/decide`는 바뀌지 않는다(항목 하나씩).

## 역할별

**Q** — `vision.py`: `response_schema=list[Observation]`, 프롬프트 §8.1(갱신본) 반영 / `observe.py`: `items` 채우고 `observation=items[0]`, 게이트는 `photo_gate_reason(items)` / `mock_vision.py`: `backend/tests/fixtures/multi_coffee_cup.json`(커피컵 4구성품) 데모 응답 / 응답 시간 확인(커피컵 9초)

**프론트** — `items`가 있으면 항목마다 `/api/decide` 호출해 카드 목록, 없으면 기존처럼 `observation` 하나 / 항목별 질문·세척 흐름 / 결과 색: `GENERAL`·`NONCOMBUSTIBLE` 빨강, 나머지 초록 / 카드 제목 `label_ko`

## 검증 (P)

- `test_coffee_cup_each_item`: 컵 본체·뚜껑 → PLASTIC, 컵홀더 → PAPER, 빨대 → GENERAL
- `photo_gate_reason`: 개인정보 아무 항목 → privacy, 작은 항목 저신뢰는 통과, 대표 항목 품질 → quality
