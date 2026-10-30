# 프로젝트 지침서 v3: "버려도 돼?" — AI 기반 상태 분석형 분리배출 도우미 (부산광역시 기준)

> **이 문서가 팀 전원이 공통으로 따르는 단일 기준(SSOT)이다.** 디자인 이미지(`docs/design-ref.png`)는 전체 흐름을 설명하기 위한 **참고용**이다.
> 팀원은 자기 AI 코딩 도구에 **이 문서와 이미지를 함께 첨부**하고 시작한다. Git·작업 방식은 저장소 루트의 `CLAUDE.md`를 따른다.
> 확정 스택: **React(Vite) + FastAPI + Google Gemini 비전 + Vercel + Supabase** / 팀 5명.

---

## 0. 에이전트(AI 코딩 도구) 작업 규칙

1. **디자인 이미지는 화면 흐름 참고용이다.** 문구·배치를 그대로 따를 필요는 없다. 이 문서와 이미지가 다르면 **이 문서가 우선**이고, 배출 방법 문구는 `rules.busan.json`(부산시 공식 안내 대조본)이 기준이다.
2. **범위 밖 기능·화면은 만들지 않는다**(§4 OUT 목록). 필요하면 명세 담당(A)에게 요청하고, 승인 후 이 문서부터 고친다.
3. **AI는 관찰만, 판단은 규칙 엔진이 한다.** Gemini에게 "어떻게 버려야 하는지"를 묻지 않는다. 배출 판단은 `backend/app/services/decide.py`와 `rules.busan.json`에서만 나온다.
4. **분리배출 규칙·출처 URL을 지어내지 않는다.** 모르는 건 `UNKNOWN`으로 처리한다.
5. **API 형식의 원본은 `backend/app/models.py`(Pydantic)** 이다. 프론트 타입(`frontend/src/lib/api-types.ts`)은 여기서 **생성**하며 손으로 고치지 않는다. 모델 변경은 A만 한다.
6. **비밀키는 서버 환경변수에만 둔다**(`GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`). 프론트 코드·`VITE_` 변수·커밋·로그에 넣지 않는다.
7. **사용자 사진 원본을 서버에 저장하거나 로그로 남기지 않는다.** Supabase에도 이미지는 저장하지 않는다(§7.3).
8. **Gemini 호출은 아껴 쓴다.** 5명이 같은 API 프로젝트 쿼터를 공유한다. 평소 개발은 `MOCK_VISION=true`로 하고, 실제 호출은 프롬프트 검증·통합 스모크 테스트에서만 한다(§17).
9. **자기 담당 폴더만 수정**한다(§14). 작은 단위로 커밋하고 **매시간 스모크 테스트(§15)** 를 돌린다.
10. 불확실한 부분은 **가정을 주석·PR 설명에 명시**하고 진행한다. 질문 때문에 멈추지 않는다.
11. 외부 코드·자료·이미지를 가져올 때는 **라이선스를 확인**한다(대회 주의사항).

---

## 1. 디자인 이미지와 구현의 관계

이미지는 5개 구역이다. **앱으로 구현하는 것은 ③번의 폰 화면들과 ④번의 결과 화면**이다. 나머지는 발표용 설명이다.

| 이미지 구역 | 역할 | 구현 여부 |
|---|---|---|
| 헤더 ("버려도 돼?", "부산광역시 기준" 배지) | 앱 이름·부제·배지 | **구현** (상단 헤더) |
| ① 입력 및 상황 확인 | 입력 데이터 설명 | 설명용 (③의 화면 1~2에 반영) |
| ② AI 분석 및 분리배출 판단 | 처리 단계 설명 | 설명용 — 단, **코드 구조는 이 5개 모듈을 따른다**(§6) |
| ③ 실행 단계별 흐름 | **폰 화면 8종 + 분기 A/B** | **구현의 핵심** (§5) |
| ④ 최종 결과 화면 예시 | **결과 화면 4종 예시** | **구현** — 데모 시나리오이자 테스트 정답(§11) |
| ⑤ 핵심 차별화 포인트 | 발표 포인트 | 설명용 (발표 슬라이드) |
| 하단 빨간 문구 | 면책 | **구현** (고정 문구, §12) |

---

## 2. 대회 컨텍스트

| 항목 | 내용 |
|---|---|
| 대회 | 2026 동아 해커톤 — "우리의 일상을 AX하라!" |
| 일정 | 10/30(금) 12:00 ~ 10/31(토) 12:00 |
| **발표자료 제출 마감** | **10/31 08:30** |
| 발표·심사 | 10/31 09:00, 팀별 5분 + 질의응답, 607호 컴퓨터 사용 → **시연 영상 폴백 필수** |
| AI 도구 | 개발·기능 모두 허용 |
| 주의사항 | 행사장 이탈 금지 / 외부 자료 라이선스 확인 / 제출 마감 엄수 |
| 심사 기준 | ①창의성·혁신성 ②기술 구현 완성도 ③실용성·UX ④팀워크 ⑤발표·시연 ("AI 활용량보다 문제 해결의 가치와 실제 구현 결과") |

개발 가능 시간은 약 18시간(10/30 14:00 ~ 10/31 08:30). **끝까지 도는 얇은 세로 한 줄**이 목표다.

---

## 3. 제품 원칙

1. **종류만이 아니라 상태를 본다**(오염·라벨·부착물·파손).
2. **AI는 관찰, 규칙은 판단.** AI 환각이 배출 결과에 직접 들어가지 않게 한다.
3. **모르면 묻거나 재촬영.** 사진이 불명확하면 억지로 결론 내지 않는다.
4. **근거 공개.** 결과 화면에 "AI 분석 결과"와 "근거 자료"를 항상 보여준다.
5. **참고용 안내.** 최종 기준은 지자체 공식 안내(§12, §13).

---

## 4. 구현 범위

### IN (이미지에 있는 것 = 전부 구현)
- 헤더: 앱 이름, 부제, "부산광역시 기준" 배지
- 화면 1~5, 분기 A(중간 결과·재촬영·재분석·최종 결과), 분기 B(일반폐기물 종료)
- 데모 품목 4종 + 세척 후 스티로폼 결과(총 5개 결과, §11)
- 결과 화면 구성: 헤드라인 / AI 분석 결과 / 배출 방법 / 근거 자료
- 하단 면책 문구
- 배포된 URL(Vercel)

### 추가 안전·운영 요소 (이미지에 없지만 필요한 최소한)
| 항목 | 이유 |
|---|---|
| 사진 불명확/개인정보 노출 시 "다시 촬영" 안내 화면 | 오판 방지, 개인정보 보호 |
| 재촬영은 **1회만** | 무한 루프 방지 |
| `규칙 미검증` 시 "시연용 규칙" 배지 + "2026년 기준" 문구 대체 | 미검증 기준을 공식 기준처럼 보이지 않게 |
| 촬영 화면 개인정보 안내 + AI 전송·미저장 고지 | 개인정보·AI 전송 고지 |
| 판단 불가(`UNKNOWN`) 안내 화면 | 지어내기 방지 |
| **익명 분석 로그를 Supabase에 저장 (P1, 화면 없음)** | 발표용 통계·디버깅. 이미지·개인정보 없음(§7.3). 실패해도 앱은 정상 동작 |
| `MOCK_VISION` 개발 모드 / 데모 모드 | Gemini 쿼터 보호, 시연 폴백. 데모 모드일 때 화면에 작은 "데모 모드" 표시 |

### OUT (만들지 않는다)
사용자 기록/히스토리 화면, 조건 변경 시뮬레이션, **신뢰도 % 화면 표시**(내부 판단용), 배출 요일·장소·시간 안내, 로그인·회원가입, 지도·수거함 위치, 포인트·리워드, 다국어, 부산 외 지역, 네이티브 앱, **서버·DB·스토리지에 사진 저장**, 프론트에서 Supabase 직접 접근

---

## 5. 화면 상태 머신 & 화면별 명세

### 5.1 상태 머신
```
REGION → CAMERA → OBSERVING ─┬─ 품질/개인정보 문제 → NOTICE_RESHOOT → CAMERA
                             └─ OK → (decide attempt=1)
        ├─ kind=ASK_QUESTION → QUESTION → RULE_LOOKUP → ┬─ kind=WASH_AND_RESHOOT → WASH_GUIDE → CAMERA(재촬영) → OBSERVING(재분석) → (decide attempt=2) → RESULT
        │                                               └─ kind=FINAL (경로 B) → RESULT (종료)
        ├─ kind=FINAL → RULE_LOOKUP → RESULT
        └─ kind=UNKNOWN → NOTICE_UNKNOWN
```
- 화면 전환은 **React Router 없이 상태 머신(useReducer 또는 zustand)** 으로 구현한다.
- `RULE_LOOKUP`의 진행 체크 애니메이션은 **연출용**이다(최소 1.2초). 실제 규칙 조회는 즉시 끝난다.
- 재촬영(`attempt=2`)의 결과는 **항상 FINAL**이다. 질문을 다시 하지 않는다.

### 5.2 화면 명세 (문구는 참고용, §12 고정 문구만 변경 금지)

| # | 화면 | 구성/문구 |
|---|---|---|
| 헤더 | 공통 | 앱 이름 **버려도 돼?** / 부제 **AI 기반 상태 분석형 분리배출 도우미** / 설명 **사진 한 장으로, 지금 이 상태의 쓰레기를 부산광역시 기준에 따라 어떻게 버려야 하는지 알려줍니다.** / 우측 배지 **부산광역시 기준 — 부산시·구·군 공식 안내 기반** |
| 1 | 지역 선택 | 제목 **지역을 선택해주세요** / 드롭다운 ① **부산광역시**(고정) ② 구·군(16개) / 버튼 **다음** |
| 2 | 사진 촬영 | 카메라 뷰/업로드(`accept="image/*" capture="environment"`), 셔터 버튼, 미리보기 후 분석 시작 |
| 3 | AI 분석 중 | 문구 **AI가 사진을 분석하고 있습니다...** / 체크 3개: **물체 인식 중 / 오염 상태 확인 중 / 부착물 확인 중** |
| 4 | 추가 확인 질문 | 질문 **이물질을 제거할 수 있나요?** / 라디오 3개: **네, 제거할 수 있어요 / 아니요, 제거할 수 없어요 / 잘 모르겠어요** |
| 5 | 지역별 규칙으로 판단 | 상단 지역 표시(핀 아이콘) **부산광역시 기준으로 판단하고 있어요...** / 체크 3개: **품목 분류 매칭 중 / 부산시·구·군 규칙 조회 중 / 최종 판단 생성 중** |
| A-6 | 중간 결과(세척 안내) | 제목 **세척 후 다시 촬영해주세요.** / 체크리스트: **남은 음식물 제거 / 물로 깨끗이 헹구기 / 이물질이 남지 않도록 세척하기** / 버튼 **세척 후 다시 촬영하기** |
| A-7 | 재촬영 후 AI 재분석 | 화면 3과 동일 |
| A-8 / B-6 / ④ | 최종 결과 | 헤드라인 / **AI 분석 결과** 불릿 / **배출 방법** 번호 목록 / **근거 자료** (§5.3) |
| B-7 | 재촬영 단계 | **진행하지 않음.** 경로 B에서는 이 화면을 만들지 않는다(결과 화면 하단 작은 글씨로 **이물질이 제거되지 않은 경우 재촬영 단계로 진행하지 않습니다.**) |
| 보완 | NOTICE_RESHOOT | 제목 **사진이 불명확해요.** / 본문 **밝은 곳에서 쓰레기 하나만 크게 다시 찍어주세요.** / (개인정보 의심 시) **얼굴이나 택배 송장 정보가 보여요. 보이지 않게 가리고 다시 찍어주세요.** / 버튼 **다시 촬영하기** |
| 보완 | NOTICE_UNKNOWN | 제목 **정확히 판단하기 어려워요.** / 본문 **거주 지역(구·군)의 최신 공식 분리배출 안내를 확인해주세요.** / 버튼 **처음으로** |
| 보완 | 오류(AI_BUSY 등) | 제목 **잠시 후 다시 시도해주세요.** / 버튼 **다시 시도** |
| 하단 | 모든 화면 | 고정 면책 문구(§12) |

### 5.3 결과 화면 구성 (이미지 ④ 기준)
```
[결과 아이콘]  {basis_label} {headline}
  예) 부산광역시 2026년 기준 투명 페트병 별도배출 대상입니다.
AI 분석 결과
  • {bullet 1} • {bullet 2} • {bullet 3} (• {bullet 4})
배출 방법
  ① {step 1}  ② {step 2}  ③ {step 3}
근거 자료
  {source.label}  (url이 있고 검증된 경우에만 링크로 표시)
[하단 면책 문구]
```
- **결과 색상:** 재활용 대상(PET_CLEAR/PLASTIC/STYROFOAM/PAPER) = 초록 체크 / 일반폐기물 = 빨강 휴지통 / 재촬영·세척 안내 = 주황
- `basis_label`: 규칙 검증됨 → **부산광역시 2026년 기준** / 미검증 → **시연용 규칙 기준** (§9.3)
- 이미지 원문의 "일반폐기물을 배출 대상입니다"는 오탈자이므로 **"일반폐기물 배출 대상입니다."** 로 쓴다.

---

## 6. 처리 파이프라인 (이미지 ② 5개 모듈 ↔ 코드)

| 이미지 모듈 | 담당 | 코드 위치 | 비고 |
|---|---|---|---|
| 물체 분석 (품목 인식, 재질 추정, 사진 특징) | AI | `backend/app/services/vision.py` → `observe()` | Gemini 호출 1회로 아래 상태 분석과 함께 수행 |
| 상태 분석 (음식물·소스 오염, 세척 가능성 단서, 부착물·파손) | AI | `vision.py` → `observe()` | |
| 추가 질문 (사진만으로 부족한 정보 확인) | AI+사용자 | `services/decide.py` → `needs_question()` | 질문 문구는 규칙 JSON에서 제공 |
| 부산 기준 조회 (구·군 기준 매칭, 품목별 규칙 조회) | 규칙 엔진 | `services/decide.py` → `lookup_rule()` | `rules.busan.json` |
| 최종 판단 (배출 종류, 행동 안내, 출처 표시) | AI+규칙 | `services/decide.py` → `decide()` | 불릿 문구는 관찰값으로 생성(§9.4) |

---

## 7. 아키텍처 & 기술 스택

### 7.1 스택 (확정)

| 영역 | 선택 |
|---|---|
| 프론트 | React 18 + Vite + TypeScript + Tailwind CSS (모바일 우선, 폰 폭 기준). 패키지 매니저 npm |
| 백엔드 | FastAPI + Pydantic v2 (Python 3.12), 업로드는 `python-multipart` |
| AI 비전 | **Google Gemini API** — 공식 SDK `google-genai`, 구조화 출력(`response_mime_type="application/json"` + `response_schema=Observation`) |
| 모델 | 환경변수 `GEMINI_MODEL` (기본값 `gemini-3.1-flash-lite`. 3.6·3.8 Flash는 무료 키 하루 20회 한도라 하루 500회인 Lite 사용 — 2026-10-30 PR #19). **A가 Google AI Studio에서 사용 가능한 모델인지 먼저 확인**하고, 지원 중단·변경 시 환경변수만 바꾼다 |
| DB | **Supabase(Postgres)** — 익명 분석 로그만(P1). **앱은 Supabase 없이도 동작해야 한다** |
| 배포 | **Vercel 단일 프로젝트**: 프론트(정적 빌드) + `api/index.py`(FastAPI 서버리스 함수). 브랜치별 프리뷰 배포 |
| 테스트 | 백엔드 `pytest`(규칙 엔진 G1~G7), 프론트 `eslint` + `tsc` |

**Vercel 단일 프로젝트로 하는 이유:** 같은 도메인이라 CORS가 필요 없고, **개인 브랜치 프리뷰 URL에서 프론트와 백엔드가 항상 같은 브랜치 코드로 함께** 돈다.

> ⚠️ **배포 검증 필요(A, 15:30까지):** Vercel의 Python(FastAPI) 함수는 요청 본문 4.5MB 제한이 있고(우리는 사진을 ≤1MB로 줄여 보내므로 충분), 함수 `maxDuration`은 `vercel.json`에서 지정한다(§부록 C). 위 구성이 **첫 배포에서 `/api/health`가 응답하는지 반드시 확인**한다. 16:00까지 안 되면 **대안: 백엔드만 Render 등으로 분리**하고 프론트의 `VITE_API_BASE`로 주소를 지정한다(비밀 아님).

### 7.2 데이터 흐름
```
브라우저: 사진 선택 → 리사이즈(긴 변 1280px) + JPEG 재인코딩(EXIF 제거)
  → POST /api/observe (multipart)  → FastAPI: Gemini 호출 → Observation 검증 → 응답 (이미지는 메모리에서만 처리 후 폐기)
  → POST /api/decide  (observation + 답변 + attempt) → FastAPI: 규칙 엔진 → Decision → (선택) Supabase 로그 insert
```
`observe`와 `decide`를 **분리**한 이유: 이미지의 "AI 분석 중"/"지역별 규칙으로 판단" 두 단계와 1:1이고, 규칙 엔진은 AI 호출 없이 독립 테스트·재호출 가능하다.

### 7.3 Supabase 사용 범위 (익명 로그, P1)
- `/api/decide`가 **최종 결과(kind=FINAL 등)를 낼 때** `analysis_logs`에 1행 insert (실패·타임아웃 1.5초 초과 시 무시).
- 저장 항목: 구·군, 품목, 결과 종류/코드, attempt, 사진 품질, 개인정보 플래그, 규칙 검증 여부, 데모 모드 여부 — **이미지·EXIF·IP·사용자 식별자·자유 텍스트 저장 금지**.
- **서버(FastAPI)에서만 service_role 키로 접근**한다. 프론트는 Supabase에 접근하지 않는다(anon 키·`VITE_SUPABASE_*` 사용 금지). RLS는 켜고 정책은 만들지 않는다.
- 테이블 SQL은 §부록 B.

### 7.4 환경변수
| 이름 | 위치 | 설명 |
|---|---|---|
| `GEMINI_API_KEY` | 서버(Vercel, `.env.local`) | 필수 |
| `GEMINI_MODEL` | 서버 | 기본 `gemini-3.1-flash-lite` |
| `MOCK_VISION` | 서버 | `true`면 Gemini 대신 고정 관찰 JSON 반환(개발·쿼터 보호·데모 폴백) |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | 서버 | 선택(없으면 로깅 건너뜀) |
| `VITE_API_BASE` | 프론트 | 기본 빈 값(같은 도메인). Render 분리 시에만 사용 |

Vercel에는 **Production과 Preview 환경 모두**에 서버 변수를 넣는다(그래야 브랜치 프리뷰가 동작한다). 값은 대시보드에만 입력하고 저장소에는 `.env.example`(이름만)을 둔다.

### 7.5 로컬 개발
```bash
# 백엔드 (저장소 루트에서)
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000 --app-dir backend
pytest backend/tests

# 프론트
cd frontend && npm install && npm run dev            # Vite가 /api 를 localhost:8000 으로 프록시
```

---

## 8. AI 관찰(Gemini) 명세

### 8.1 시스템 프롬프트 (그대로 사용, 수정은 P 승인 — 2026-10-30 여러 항목용으로 갱신)
```
당신은 "분리배출 사진 관찰기"입니다.
사진에 보이는 분리배출 대상 각각에 대해 종류, 재질, 오염 및 부착물 상태를 관찰해 JSON으로만 보고합니다.

규칙:
1. 어떻게 버려야 하는지(배출 방법·분류)는 절대 판단하거나 언급하지 마세요. 그것은 다른 시스템이 합니다.
2. 사진에서 확인되지 않는 것은 추측하지 말고 "unknown"으로 표기하세요.
3. 사진이 흐리거나 어둡거나 대상이 일부만 보이면 photo_quality에 반영하고 confidence를 낮추세요.
4. 사람의 얼굴, 택배 송장의 이름·주소·전화번호 등 개인정보가 보이면 privacy_flag를 true로 하세요. 그 내용을 출력에 옮겨 적지 마세요.
5. 제품의 브랜드명·상표는 기록하지 마세요.
6. 출력은 지정된 스키마의 JSON 배열 하나뿐입니다. 설명 문장, 마크다운, 코드블록을 붙이지 마세요.
7. 항목은 '물건'이 아니라 '따로 버려야 하는 재질 단위'로 셉니다. 제품 포장은 포장재마다 별도 항목으로 보고하세요: 용기·본체, 캡·뚜껑, 포장 비닐·필름, 라벨, 빨대·컵홀더 등. 사진에 다른 물건이 함께 있어도 모든 물건에 똑같이 적용하세요. 예) 물티슈 → 물티슈 본체 + 플라스틱 캡 + 포장 비닐 / 컵 → 컵 본체 + 뚜껑 + 빨대 + 컵홀더. 큰 것부터 최대 6개까지 보고하세요.
8. 재질 구분 단서: 종이는 무광·결·접힌 모서리, 스티로폼(EPS)은 거친 알갱이 무늬, 플라스틱은 매끈함·광택·이음선. 불분명하면 unknown으로 쓰세요.
9. label_ko에는 브랜드 없이 짧은 이름(예: "컵 뚜껑")을 쓰세요.
```

### 8.2 `Observation` (Pydantic — `backend/app/models.py`가 원본)
```python
from typing import Literal
from pydantic import BaseModel

Tri = Literal["yes", "no", "unknown"]     # bool 대신 문자열 3값 (Gemini 스키마 호환 + 모호함 표현)

class Contamination(BaseModel):
    level: Literal["none", "light", "heavy", "unknown"]
    type: Literal["food", "sauce", "oil", "dirt", "none", "unknown"]
    likely_removable_by_rinsing: Tri

class Attachments(BaseModel):
    label_present: Tri        # 라벨·스티커
    tape_present: Tri         # 테이프
    waybill_present: Tri      # 택배 송장
    lid_present: Tri          # 뚜껑

class Observation(BaseModel):
    item_type: Literal["pet_bottle", "styrofoam_container", "plastic_container",
                       "cardboard_box", "other", "unknown"]
    material_guess: Literal["PET", "EPS", "PP", "PS", "paper", "mixed", "unknown"]
    is_transparent_colorless: Tri     # 페트병: 무색 투명 여부
    is_white: Tri                     # 스티로폼: 흰색(유색 아님) 여부
    contents_present: Tri             # 병/용기 안에 내용물이 남아 있는지
    contamination: Contamination
    attachments: Attachments
    damage: Literal["none", "broken", "crushed", "unknown"]
    coating_or_mixed_material: Tri    # 코팅·타 재질 혼합
    privacy_flag: bool                # 얼굴·송장 개인정보 노출 의심
    photo_quality: Literal["good", "blurry", "dark", "partial"]
    confidence: float                 # 0.0~1.0, 내부 판단용(화면 표시 금지). 서버에서 0~1로 clamp
    notes_ko: str                     # 관찰 한 문장(판단·배출 방법 언급 금지)
```
- 프론트의 `Observation` 타입은 이 모델에서 **생성**한다(§14 계약 동기화).
- Gemini 호출: `temperature=0`, 타임아웃 20초. 응답은 `response.parsed`(Pydantic)로 받고, 검증 실패 시 1회 재시도 후 `photo_quality="partial"`, `confidence=0`으로 대체해 "다시 촬영" 경로로 보낸다. 지연이 길면 `thinking_budget=0` 같은 설정을 모델이 지원하는 범위에서 검토한다.
- **`RESOURCE_EXHAUSTED`(429)·타임아웃** → 1회 짧게 재시도 후 `503 AI_BUSY`. 프론트는 "잠시 후 다시 시도해주세요" 화면(§5.2)을 보여준다.

---

## 9. 규칙 엔진 명세

### 9.1 `decide(observation, region, answers, attempt)` 라우팅표 (위에서 아래로 첫 매칭)

**공통 게이트 (모든 품목)**
1. `privacy_flag == True` → `RESHOOT_QUALITY(privacy)`
2. `photo_quality != "good"` 또는 `confidence < 0.6` → `RESHOOT_QUALITY(quality)`
3. `item_type ∈ {other, unknown}` → `UNKNOWN`

**품목별** (값 비교는 `"yes"/"no"/"unknown"` 문자열)
| item_type | 조건 | 결과 |
|---|---|---|
| `pet_bottle` | `is_transparent_colorless == "yes"` | `FINAL(PET_CLEAR)` |
| | 그 외(유색·불명) | `FINAL(PLASTIC)` *(확장)* |
| `styrofoam_container` | `is_white == "no"` 또는 `coating_or_mixed_material == "yes"` | `FINAL(GENERAL)` *(확장)* |
| | `contamination.level == "none"` | `FINAL(STYROFOAM)` |
| | 오염 있음 & `attempt==1` & 답변 없음 | `ASK_QUESTION` |
| | 오염 있음 & 답변 `"yes"` | `WASH_AND_RESHOOT` |
| | 오염 있음 & 답변 `"no"` 또는 `"unknown"` | `FINAL(GENERAL)` + 불릿 "오염 제거 어려움 (사용자 답변)" |
| | 오염 있음 & `attempt==2` | `FINAL(GENERAL)` + 불릿 "세척 후에도 오염이 남아 있음" |
| `plastic_container` | `coating_or_mixed_material == "yes"` | `FINAL(GENERAL)` *(확장)* |
| | `contamination.level == "none"` | `FINAL(PLASTIC)` |
| | 오염 있음 | 스티로폼과 **동일한 질문·재촬영 로직**(ASK → WASH → GENERAL/PLASTIC) *(확장)* |
| `cardboard_box` | 음식물·기름 오염(`level≠none`, type∈{food,sauce,oil}) | `FINAL(GENERAL)` *(확장)* |
| | `coating_or_mixed_material == "yes"` | `FINAL(GENERAL)` *(확장)* |
| | 그 외 | `FINAL(PAPER)` |
| `can` *(확장, 2026-10-30)* | 항상 (내용물·오염은 헹구면 됨) | `FINAL(CAN)` |
| `vinyl` *(확장)* | 오염 있음 | `FINAL(GENERAL)` (이물질 묻은 비닐은 종량제) |
| | 그 외 | `FINAL(VINYL)` |
| `glass_bottle` *(확장)* | `damage == "broken"` | `FINAL(NONCOMBUSTIBLE)` (깨진 유리는 불연성 마대) |
| | 그 외 | `FINAL(GLASS)` |
| `paper_pack` *(확장)* | 항상 (종이류와 따로) | `FINAL(PAPER_PACK)` |
| `wet_tissue` *(확장)* | 항상 | `FINAL(GENERAL)` — 근거: 인천시 공식 안내(2026-07-30), 부산시 안내에 없음 |
| *(공통)* 복합 제품 | `material_guess=="mixed"` 또는 이름(`label_ko`)에 "패키지"·"세트" | 어떤 `FINAL`이든 배출 방법 끝에 "뚜껑·포장 비닐·라벨처럼 재질이 다른 부분이 붙어 있으면 떼어서 각각의 재질대로 분리배출하기" 한 줄 추가 |
| `general_waste` *(확장)* | 항상 (사용한 휴지·폐휴지, 기저귀, 부직포, 벽지) | `FINAL(GENERAL)` — 부산시 종이류 안내 |
| `noncombustible_item` *(확장)* | 항상 (사기그릇·도자기, 조개껍데기, 동물 뼈) | `FINAL(NONCOMBUSTIBLE)` — 부산시 불연성 안내 |
| `receipt_coated_paper` *(확장)* | 항상 (영수증·전표·코팅지는 종이류 아님) | `FINAL(GENERAL)` |
| `other` + `material_guess == "paper"` *(보완)* | `cardboard_box`와 동일 | `FINAL(PAPER)` / `FINAL(GENERAL)` |

- 재촬영 결과(`attempt==2`)에서 오염이 없으면 `FINAL(STYROFOAM)` 또는 `FINAL(PLASTIC)`, 오염 불릿은 **"음식물·소스 오염 없음 (세척 완료)"**.
- "잘 모르겠어요"는 "아니요"와 동일하게 처리한다(보수적).
- *(확장)* 표시는 이미지에 직접 없지만 같은 논리로 필요한 최소 분기다. 발표에서 강조하지 않는다.

### 9.2 결과 모델 (Pydantic — `backend/app/models.py`)
```python
DecisionKind = Literal["ASK_QUESTION", "WASH_AND_RESHOOT", "FINAL", "RESHOOT_QUALITY", "UNKNOWN"]
ResultCode = Literal["PET_CLEAR", "PLASTIC", "STYROFOAM", "PAPER", "GENERAL"]

class QuestionOption(BaseModel):
    v: Literal["yes", "no", "unknown"]
    l: str

class Question(BaseModel):
    text: str
    options: list[QuestionOption]

class Source(BaseModel):
    label: str
    url: str | None = None

class Decision(BaseModel):
    kind: DecisionKind
    result_code: ResultCode | None = None
    basis_label: str                       # §9.3
    headline: str
    analysis_bullets: list[str] = []
    steps: list[str] = []
    question: Question | None = None
    wash_checklist: list[str] | None = None
    reshoot_reason: Literal["quality", "privacy"] | None = None
    source: Source
    rules_verified: bool
    terminal: bool
```

### 9.3 `backend/app/rules/rules.busan.json` — 문구 데이터 (시드)

> ✅ **2026-10-30 부산광역시 공식 안내와 대조 완료 → `busan_verified: true`.** 출처: https://www.busan.go.kr/depart/ahwastepolicy09 (자원순환과, 2026-10-02 업데이트), https://www.busan.go.kr/nhot/881417 (자원순환과, 2017-08-25). 대조 메모는 `rules.busan.json`의 `verification` 항목. **최신 값은 저장소의 `backend/app/rules/rules.busan.json`이 기준이며 아래 JSON은 최초 시드 기록이다.**
> 규칙을 다시 바꿀 때도 같은 절차를 따른다: ① `busan_verified:true` ② `source_url`에 **실제로 확인한 부산시 공식 URL**만 기입 ③ `basis_label`이 자동으로 "부산광역시 2026년 기준"으로 바뀐다. **URL을 추측해서 채우지 말 것.**

```json
{
  "region": "busan",
  "version": "seed-2026-10-30",
  "busan_verified": false,
  "basis_label_verified": "부산광역시 2026년 기준",
  "basis_label_unverified": "시연용 규칙 기준",
  "results": {
    "PET_CLEAR": {
      "headline": "투명 페트병 별도배출 대상입니다.",
      "steps": ["내용물을 완전히 비우고 헹구기", "라벨 제거하기", "압착 후 투명 페트병으로 분리배출하기"],
      "source_label": "부산광역시 재활용품 분리배출 안내", "source_url": null
    },
    "PLASTIC": {
      "headline": "플라스틱류 분리배출 대상입니다.",
      "steps": ["내용물 비우기", "라벨·스티커 제거하기", "플라스틱류로 분리배출하기"],
      "source_label": "부산광역시 재활용품 분리배출 안내", "source_url": null
    },
    "STYROFOAM": {
      "headline": "스티로폼류 분리배출 대상입니다.",
      "steps": ["내용물을 완전히 비우고 세척하기", "뚜껑 제거 후 건조하기", "부산시 스티로폼 기준에 따라 분리배출하기"],
      "source_label": "부산광역시 스티로폼류 분리배출 안내", "source_url": null
    },
    "PAPER": {
      "headline": "종이류 분리배출 대상입니다.",
      "steps": ["테이프·송장 제거하기", "상자를 펼쳐 납작하게 하기", "종이류로 분리배출하기"],
      "source_label": "부산광역시 재활용품 분리배출 안내", "source_url": null
    },
    "GENERAL": {
      "headline": "일반폐기물 배출 대상입니다.",
      "steps": ["내용물을 비우고", "오염 제거가 어려우면 재활용 제외", "종량제 봉투에 넣어 배출하기"],
      "source_label": "부산광역시 재활용품 분리배출 안내", "source_url": null
    }
  },
  "question": {
    "text": "이물질을 제거할 수 있나요?",
    "options": [
      { "v": "yes", "l": "네, 제거할 수 있어요" },
      { "v": "no", "l": "아니요, 제거할 수 없어요" },
      { "v": "unknown", "l": "잘 모르겠어요" }
    ]
  },
  "wash_guide": {
    "headline": "세척 후 다시 촬영해주세요.",
    "checklist": ["남은 음식물 제거", "물로 깨끗이 헹구기", "이물질이 남지 않도록 세척하기"],
    "button": "세척 후 다시 촬영하기"
  }
}
```
- 규칙 담당(D)은 **지자체별로 안내가 다를 수 있는 항목**(예: 음식물이 묻은 플라스틱 용기를 "씻어서 배출"로 안내하는 곳과 "종량제"로 안내하는 곳이 모두 있음)을 우선 부산시 공식 안내와 대조한다.

### 9.4 "AI 분석 결과" 불릿 생성 규칙 (`services/bullets.py`)

관찰값으로 아래 순서·문구로 만든다(해당 없는 줄은 생략, 최대 4줄).

| 줄 | 규칙 |
|---|---|
| 품목 | `pet_bottle`: **페트병 (투명)** / **페트병 (유색)** · `styrofoam_container`: **스티로폼 용기** · `plastic_container`: **플라스틱 용기 (PP 추정)**(`material_guess=="PP"`) 아니면 **플라스틱 용기** · `cardboard_box`: **종이상자 (골판지)** |
| 오염/내용물 | 병: **내용물 없음** / **내용물 있음** · 용기: 오염 없음 → **오염 없음 (깨끗함)**, 재촬영 후 깨끗 → **음식물·소스 오염 없음 (세척 완료)**, 오염 있음 → **음식물·소스 오염 있음** · 종이상자: **오염 없음, 재활용 가능** |
| 부착물 | `label_present=="yes"` → **라벨 부착 있음** · `tape_present=="yes"` → **테이프 부착 있음** · 둘 다 없음(플라스틱 용기) → **라벨·부착물 없음** |
| 파손 | `damage=="none"` → **파손 없음** (병·스티로폼·플라스틱 용기만 표시) |
| 사용자 답변 | 답변이 "아니요/잘 모르겠어요"로 GENERAL이 된 경우 → **오염 제거 어려움 (사용자 답변)** |

---

## 10. API 명세 (FastAPI)

모든 경로는 `/api` 접두사를 쓴다(로컬·Vercel 동일). 로컬에서는 `/docs`(Swagger), `/openapi.json`으로 확인한다.

### `GET /api/health` → `{ "ok": true }` (배포·스모크 테스트용)

### `POST /api/observe`
- `multipart/form-data`: `image`(JPEG, ≤ 3MB), `is_reshoot`(optional bool)
- **200:** `{ observation: Observation, items?: Observation[], ok: bool, reason?: "quality" | "privacy", demo_mode: bool }`
  - *(2026-10-30 여러 항목)* `items` = 사진 속 항목들(큰 것부터 최대 6개), `observation` = `items[0]`(하위 호환). 프론트는 항목마다 `/api/decide`를 호출한다
  - `ok/reason`은 `services.decide.photo_gate_reason(items)`: 개인정보는 어느 항목이든, 품질은 대표 항목(`items[0]`)만
  - `ok=false`는 §9.1 공통 게이트 1·2에 걸린 경우(서버가 판정)
  - `demo_mode=true`는 `MOCK_VISION`일 때(프론트는 작은 "데모 모드" 표시)
- **에러:** `400`(이미지 없음/형식), `413`(용량), `503 AI_BUSY`(쿼터/타임아웃), `502`(AI 응답 불가), `500`
- 이미지는 요청 처리 중 메모리에만 존재하며 **저장·로깅하지 않는다.**

### `POST /api/decide`
- JSON: `{ region: { sido: "부산광역시", gu: str }, observation: Observation, answers?: { contamination_removable?: "yes"|"no"|"unknown" }, attempt: 1 | 2, demo_mode?: bool }`
- **200:** `Decision` (§9.2)
- AI를 호출하지 않는다(규칙만) → 빠르고 단위 테스트 가능. 입력은 Pydantic으로 검증된다.

### 구·군 목록 (16개, 드롭다운 값)
강서구, 금정구, 기장군, 남구, 동구, 동래구, 부산진구, 북구, 사상구, 사하구, 서구, 수영구, 연제구, 영도구, 중구, 해운대구
(MVP 규칙은 부산 공통 1벌이며 `gu`는 화면 표시·로그용이다.)

---

## 11. 골든 아웃풋 (이미지 ④·③에서 옮긴 정답 — 테스트 기준)

`decide()` 결과가 아래와 **헤드라인·배출 방법은 문자열 그대로**, **AI 분석 결과는 해당 문구를 포함**해야 한다(`basis_label`은 별도).

| ID | 입력 상황 | kind / code | headline | AI 분석 결과 | 배출 방법 |
|---|---|---|---|---|---|
| G1 | 투명 페트병, 라벨 부착, 내용물 없음 | FINAL / PET_CLEAR | 투명 페트병 별도배출 대상입니다. | 페트병 (투명) · 라벨 부착 있음 · 내용물 없음 · 파손 없음 | ① 내용물을 완전히 비우고 헹구기 ② 라벨 제거하기 ③ 찌그러뜨리고 뚜껑 닫아 투명 페트병 전용 수거함에 배출하기 |
| G2 | 스티로폼 용기, 소스 오염, 첫 촬영 | ASK_QUESTION | — | — | 질문: 이물질을 제거할 수 있나요? |
| G3 | G2 + 답변 "아니요" (경로 B) | FINAL / GENERAL | 일반폐기물 배출 대상입니다. | 스티로폼 용기 · 음식물·소스 오염 있음 · 오염 제거 어려움 (사용자 답변) | ① 내용물을 비우고 ② 오염 제거가 어려우면 재활용 제외 ③ 종량제 봉투에 넣어 배출하기 |
| G4 | G2 + 답변 "네" (경로 A) | WASH_AND_RESHOOT | 세척 후 다시 촬영해주세요. | — | 체크리스트: 남은 음식물 제거 / 물로 깨끗이 헹구기 / 이물질이 남지 않도록 세척하기 |
| G5 | G4 후 재촬영, 깨끗한 스티로폼 (`attempt=2`) | FINAL / STYROFOAM | 스티로폼류 분리배출 대상입니다. | 스티로폼 용기 · 음식물·소스 오염 없음 (세척 완료) · 파손 없음 | ① 내용물을 완전히 비우고 세척하기 ② 테이프·운송장 제거하기 ③ 스티로폼류로 분리배출하기 |
| G6 | 플라스틱 용기, 깨끗함(PP 추정) | FINAL / PLASTIC | 플라스틱류 분리배출 대상입니다. | 플라스틱 용기 (PP 추정) · 오염 없음 (깨끗함) · 라벨·부착물 없음 · 파손 없음 | ① 내용물 비우기 ② 라벨·스티커 제거하기 ③ 플라스틱류로 분리배출하기 |
| G7 | 택배 종이상자, 테이프 부착, 오염 없음 | FINAL / PAPER | 종이류 분리배출 대상입니다. | 종이상자 · 테이프 부착 있음 · 오염 없음, 재활용 가능 | ① 테이프·송장 제거하기 ② 상자를 펼쳐 납작하게 하기 ③ 종이류로 분리배출하기 |
| G8 *(확장)* | 빈 음료 캔 | FINAL / CAN | 캔류 분리배출 대상입니다. | 캔 (금속) · 내용물 없음 · 파손 없음 | ① 내용물을 비우고 헹구기 ② 플라스틱 뚜껑 등 다른 재질은 분리하기 ③ 캔류로 분리배출하기 |
| G9 *(확장)* | 깨끗한 과자 봉지 | FINAL / VINYL | 비닐류 분리배출 대상입니다. | 비닐류 · 이물질 없음 | ① 물기·음식물 등 이물질 제거하기 ② 여러 장은 한 봉투에 모으기 ③ 비닐류로 분리배출하기 |
| G10 *(확장)* | 빈 유리 음료병 | FINAL / GLASS | 유리병류 분리배출 대상입니다. | 유리병 · 내용물 없음 · 파손 없음 | ① 내용물을 비우고 헹구기 ② 뚜껑 분리하기 (보증금 표시 소주·맥주병은 마트에 반환 가능) ③ 유리병류로 분리배출하기 |
| G11 *(확장)* | 빈 우유팩 | FINAL / PAPER_PACK | 종이팩 분리배출 대상입니다. | 종이팩 (우유·주스팩) · 내용물 없음 | ① 내용물 비우기 ② 종이류와 섞지 말고 따로 모으기 ③ 종이팩 전용 배출함에 배출하기 (없으면 묶어서 배출) |

**게이트 테스트:** 흐린 사진 → RESHOOT_QUALITY(quality) / 얼굴·송장 노출 → RESHOOT_QUALITY(privacy) / 판별 불가 물체 → UNKNOWN

`backend/tests/test_decide.py`에 **G1~G7을 단위 테스트(관찰 JSON 픽스처 → 기대 Decision)** 로 둔다. Gemini 정확도와 무관하게 규칙 엔진 정답을 먼저 고정하기 위함이다. 같은 픽스처를 `MOCK_VISION`의 고정 관찰 응답으로 재사용한다.

---

## 12. 고정 문구 (변경 금지)

- **하단 면책(모든 화면, 이미지 원문):**
  `이 화면은 시연용 예시입니다. 실제 서비스에서는 부산시와 각 구·군의 최신 공식 공지사항을 기준으로 제공합니다. 배출 요일과 장소는 지역별로 다를 수 있으므로 거주 지역의 최신 안내를 반드시 확인하세요.`
- **규칙 미검증 배지(`rules_verified=false`일 때 결과 화면 상단 작은 글씨):**
  `시연용 규칙 · 부산시 공식 기준 대조 전`
- **촬영 화면 안내:**
  `쓰레기 하나만 크게 찍어주세요. 사람 얼굴이나 택배 송장의 이름·주소·전화번호가 보이지 않게 해주세요.`
  `사진은 분석을 위해 Google Gemini API로 전송되며, 본 서비스는 사진을 저장하지 않습니다. 개인정보가 담긴 사진은 올리지 마세요.`
- **데모 모드 표시(`demo_mode=true`):** `데모 모드` (결과 화면 상단 작은 글씨)
- "100% 정확", "인증", "공식 서비스" 같은 표현은 어디에도 쓰지 않는다.

---

## 13. 법적·윤리 가이드라인 (구현 규칙)

> 법률 자문이 아니라 해커톤 수준에서 위험을 줄이는 설계 규칙이다. 정식 서비스 전에는 전문가 검토가 필요하다.

1. **참고용 안내:** 적법 배출·과태료 면제를 보증하지 않는다. 면책 문구 고정(§12).
2. **공식성 오인 방지:** 부산광역시·구·군·환경부 등 **기관 로고·휘장을 쓰지 않는다.** 출처는 텍스트로만 표기한다. **검증하지 않은 URL을 근거 자료 링크로 걸지 않는다.**
3. **미검증 표시:** `busan_verified=false`이면 "시연용 규칙" 배지와 `basis_label_unverified`를 반드시 쓴다. "2026년 기준"은 검증 후에만.
4. **개인정보 최소화:** 로그인·이름·연락처·정확한 위치 수집 없음 / 사진 원본 미저장(디스크·DB·스토리지·로그 모두) / 클라이언트 재인코딩으로 EXIF 제거 / 얼굴·송장 노출 시 재촬영 유도 / 에러 로그에 이미지·base64 출력 금지 / **Supabase 로그에도 이미지·식별자·IP 저장 금지**.
5. **Gemini 무료 티어 주의:** 무료 티어에서는 입력이 Google의 모델 개선에 쓰일 수 있고 사람이 검토할 수 있다는 안내가 있다(요금제 문서 기준, 정책은 변경될 수 있으므로 A가 현재 약관 확인). 따라서 **개발·시연 중 업로드하는 사진은 팀이 직접 찍은, 사람·개인정보가 없는 쓰레기 사진만** 쓴다. 타인 사진·얼굴·송장 사진을 테스트에 쓰지 않는다. 정식 서비스는 유료 티어·약관 검토가 필요하다.
6. **외부 AI 전송 고지:** 촬영 화면 고정 문구(§12).
7. **상표·저작권:** 시연 사진은 **팀이 직접 촬영**하고, 제품 라벨·로고가 보이면 가리거나 제거한 뒤 촬영한다. 인터넷·제조사 이미지 사용 금지. (디자인 이미지에도 실제 브랜드 라벨이 보이므로 **발표 슬라이드에 쓰기 전에 가리거나 재생성**한다.)
8. **AI 생성 목업 이미지**는 발표에서 "예시 화면"으로 표기한다.
9. **공공데이터**(배출 요일 등)는 MVP에서 쓰지 않는다. 쓰려면 공식 출처와 이용 조건을 먼저 확인한다.
10. 앱 이름 "버려도 돼?"는 가칭이며 기존 상표·앱 이름과의 중복은 확인하지 않았다.

---

## 14. 폴더 구조 & 역할 분담 (팀 5명)

```
/                              ← 저장소 루트 = Vercel 프로젝트 루트
  CLAUDE.md                    ← 작업·Git 규칙
  vercel.json                  ← 빌드/함수 설정 (A)
  requirements.txt             ← 서버 의존성 (Vercel이 설치) (A)
  requirements-dev.txt         ← pytest 등 개발 전용 (A)
  .env.example                 ← 변수 이름만 (A)
  /api
    index.py                   ← Vercel 진입점: backend 앱을 불러옴 (A)
  /backend
    /app
      main.py                  ← FastAPI 앱·라우터 등록 (A)
      models.py                ← Pydantic 모델 = API 계약 원본 (A)
      /routers
        observe.py             ← C
        decide.py              ← D
      /services
        vision.py              ← Gemini 호출·검증·재시도 (C)
        mock_vision.py         ← MOCK_VISION 고정 응답 (C)
        log.py                 ← Supabase 익명 로그 (C)
        decide.py              ← 규칙 엔진 (D)
        bullets.py             ← 불릿 생성 (D)
      /rules
        rules.busan.json       ← D (내용 변경은 A와 합의)
    /tests
      test_decide.py           ← G1~G7 (D)
  /frontend                    ← Vite + React + TS + Tailwind
    package.json, vite.config.ts   ← A
    /src
      /screens                 ← B (화면 1~5, A-6, 결과, 보완 화면)
      /components              ← B (Header, ProgressChecks, ResultCard, Footer ...)
      /lib
        image.ts               ← B (리사이즈·EXIF 제거)
        api.ts                 ← B (fetch 래퍼)
        api-types.ts           ← **생성 파일** (A만 재생성, 손으로 수정 금지)
  /samples                     ← D (직접 촬영 정리본 + 기대 결과)
  /docs
    PROJECT_SPEC.md, design-ref.png, slides/
```

| 역할 | 담당 업무 |
|---|---|
| **A. 통합·배포** | `models.py`(계약), 계약 동기화(아래), Vercel·Supabase 설정, 환경변수, 배포 검증, PR 병합, 매시간 스모크 테스트 |
| **B. 프론트** | 화면 상태 머신(§5), 촬영/업로드, 진행 체크 애니메이션, 반응형, API 연결 |
| **C. 백엔드·판독** | `/api/observe`, Gemini 연동·프롬프트 검증, `MOCK_VISION`, 에러 처리, Supabase 로그 |
| **D. 규칙·데이터** | `decide.py`·`bullets.py`·규칙 JSON·G1~G7 테스트, 샘플 사진 촬영·정답표, **부산시 공식 기준 대조** |
| **E. 발표·시연** | 슬라이드(이미지 ①②⑤ 활용), 시연 시나리오·영상, 리허설, 샘플 사진 촬영 지원 |

**계약 동기화 (A, 모델이 바뀔 때마다):**
```bash
# 백엔드가 로컬에서 떠 있는 상태에서
cd frontend && npx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api-types.ts
```
생성 후 프론트 타입 오류가 나면 B에게 알린다. **모델 변경은 항상 팀 채팅에 먼저 공지**한다.

---

## 15. 타임라인 & 수용 기준

| 시간 | 할 일 |
|---|---|
| ~15:30 | **A:** 저장소·`main` 보호, Vercel 프로젝트(단일) 생성, 빈 프론트 + `/api/health` **첫 배포 검증**, Supabase 프로젝트·테이블 생성(§부록 B), 환경변수 입력(Production+Preview), Gemini 모델 사용 가능 여부 확인, `models.py` 초안·`.env.example` 푸시. **전원:** clone, 개인 브랜치 생성, 이 문서+이미지 숙지, **E 포함 샘플 사진 촬영 시작** |
| 15:30~16:30 | **C:** Gemini 프롬프트 검증(샘플 20장+, 4품목 × 깨끗/오염), `MOCK_VISION` 구현 / **D:** `decide.py` + G1~G7 테스트 / **B:** 화면 뼈대·상태 머신 / **A:** Vercel 배포 불가 시 16:00에 Render 대안 결정 |
| 16:30까지 | **모두 스켈레톤을 `main`에 한 번 머지**해 연결 경로를 먼저 뚫는다 |
| 16:30~01:00 | 화면 1→5→결과 연결, 분기 A/B, 재촬영 — 매시간 스모크 테스트 |
| **01:00** | **기능 동결**(버그 수정만), 교대 수면 시작 |
| 01:00~04:00 | 안정화, 모바일 UI, 오류·보완 화면, 폴백, **Gemini 쿼터 확인** |
| 04:00~06:00 | 시연 영상 녹화, 발표자료 완성 |
| 06:00~07:30 | 5분 타이머 리허설 2회 이상 |
| 07:30~08:15 | 최종 점검 → **08:15 전 제출** (마감 08:30) |

**스모크 테스트(매시간, 배포 URL에서):** G1, G2→G3, G2→G4→G5, G6, G7을 끝까지 돌린다. 코드가 돌아가는 것과 *데모 경로가 도는 것*은 다르다. (평소엔 `MOCK_VISION`, 실제 Gemini 경로는 A가 하루 몇 번만.)

**수용 기준**
- [ ] 배포 URL에서 모바일 브라우저로 G1~G7 시나리오가 끝까지 동작한다
- [ ] 경로 A(세척→재촬영→재분석→최종)와 경로 B(일반폐기물 종료) 모두 동작한다
- [ ] 결과 문구가 `/api/decide` 응답과 일치하고, §12 고정 문구가 들어가 있다
- [ ] 흐린 사진/개인정보 노출 시 "다시 촬영" 안내가 나온다
- [ ] 모든 결과 화면에 AI 분석 결과·배출 방법·근거 자료·면책 문구가 있다
- [ ] `busan_verified=false`일 때 "시연용 규칙" 배지가 보인다
- [ ] 서버·로그·DB·저장소에 사진 원본과 API 키가 없다
- [ ] Gemini 실패(`AI_BUSY`) 시 오류 안내가 나온다(빈 화면 금지)
- [ ] Supabase가 꺼져 있어도 앱이 정상 동작한다
- [ ] `pytest`(G1~G7) 통과, 프론트 `tsc`·`lint`·`build` 통과
- [ ] 시연 영상(폴백)이 준비돼 있다

---

## 16. 발표 가이드 (5분)

| 시간 | 내용 |
|---|---|
| 0:00~0:40 | 공감 도입: "이 스티로폼, 어디에 버려야 하죠?" |
| 0:40~1:10 | Before → DX(분류표·검색형) → AX(상태 판단) 한 장 |
| 1:10~3:40 | 시연: **같은 스티로폼, 상태에 따라 결과가 달라진다**(G2→G3 / G2→G4→G5), 이어서 페트병(G1) 짧게 |
| 3:40~4:30 | 구조 "AI는 관찰, 규칙은 판단, 근거는 공개" + 한계(부산 공식 기준 대조 단계, 구·군별 기준은 확장) |
| 4:30~5:00 | 팀 역할, 마무리 한 문장 |

이미지 ⑤의 4가지 차별화(상태 판단 / 부산 기준 / AI+규칙 엔진 / 재촬영 재판단)를 그대로 쓴다.

**예상 질문**
- *"기존 분리배출 앱과 뭐가 다른가요?"* → 환경부 계열 '내 손안의 분리배출' 앱이 있다(기능 상세는 미확인). 우리는 품목 검색이 아니라 사진 속 상태를 보고, 재촬영으로 재판단하며, 근거를 공개한다. **"기존 서비스가 없다"고 말하지 않는다.**
- *"AI가 틀리면요?"* → AI는 관찰만, 판단은 규칙. 불명확하면 재촬영·질문, 최종 확인은 공식 안내.
- *"부산 기준이 맞나요?"* → **검증한 범위만 말한다.** 대조가 끝나지 않았다면 "공통 원칙 기반 시연 규칙이며 공식 기준 연동은 확장 과제"라고 말한다.
- *"개인정보는요?"* → 로그인 없음, 사진 미저장, 얼굴·송장 노출 시 재촬영 유도, DB에는 익명 통계만.
- *"Supabase는 왜 쓰나요?"* → 익명 분석 통계(품목별 결과 분포 등)용. 사진·개인정보는 저장하지 않는다.

---

## 17. 리스크 & 폴백

| 리스크 | 대응 |
|---|---|
| **Gemini 쿼터 소진(5명이 한 프로젝트 쿼터 공유)** | 개발은 `MOCK_VISION=true`, 실제 호출은 프롬프트 검증·스모크 테스트만. 호출 수를 줄이려 같은 사진 반복 테스트 금지. 발표 당일 아침 쿼터 확인, **`MOCK_VISION`/데모 모드로 폴백**(화면에 "데모 모드" 표시) |
| Gemini 지연/실패 | 타임아웃 20초 + 1회 재시도 + `AI_BUSY` 안내, 시연 영상 폴백 |
| Vercel Python 함수 배포 문제 | 15:30 첫 배포 검증, 16:00 안 되면 백엔드만 Render로 분리(`VITE_API_BASE`) |
| Gemini 모델명 변경·중단 | `GEMINI_MODEL` 환경변수로 교체, A가 사전에 확인 |
| 현장 네트워크 불안 | 시연 영상 필수, 샘플 사진은 클라우드와 USB 양쪽 보관 |
| 오염 판독 오류 | 신뢰도 임계값 0.6 + 질문/재촬영 경로, 시연용 사진은 사전 테스트로 안정적인 것만 사용 |
| 부산 공식 기준 대조 미완료 | 배지·`basis_label` 대체, 발표에서 명시 |
| 모델(계약) 변경으로 프론트/백엔드 불일치 | A만 `models.py` 수정 + 변경 공지 + 타입 재생성 |
| 범위 팽창 | 01:00 기능 동결, §4 OUT 목록 엄수 |

---

## 부록 A. 규칙 시드 참고 출처 (부산시 공식 기준 아님)

- 환경부 재활용품 분리배출 가이드라인(지자체가 일부 내용을 보완하도록 한 공통 가이드): https://www.incheon.go.kr/media/4/11299
- 파주시 재활용품 배출요령: https://www.paju.go.kr/www/www_02/environment/environment_05/environment_05_01/environment_05_01_02.jsp
- 구리시 재활용품 분리배출요령: https://www.guri.go.kr/environment/contents.do?key=1381
- 연수구 재활용품 배출요령(지자체별 차이 예시): https://www.yeonsu.go.kr/main/part/clean/recycle.asp
- 서울시 투명 페트병 분리배출 안내: https://mediahub.seoul.go.kr/archives/1502648

**완료(P, 2026-10-30):** 부산광역시 공식 안내와 대조해 `source_url` 기입, `busan_verified: true`. 구·군별 세부 기준 대조는 확장 과제.

## 부록 B. Supabase 테이블 (A가 SQL Editor에서 1회 실행)

```sql
create table public.analysis_logs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  gu text,
  item_type text,
  kind text not null,
  result_code text,
  attempt smallint,
  photo_quality text,
  privacy_flag boolean,
  rules_verified boolean,
  demo_mode boolean not null default false
);

alter table public.analysis_logs enable row level security;
-- 정책을 만들지 않는다. service_role 키(서버 전용)만 접근한다. anon 키는 사용하지 않는다.
```

## 부록 C. 참고 구현 스니펫 (검증 필요 — A·C가 첫 배포·첫 호출에서 확인)

**`vercel.json`** (저장소 루트)
```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "functions": { "api/index.py": { "maxDuration": 60 } },
  "rewrites": [ { "source": "/api/(.*)", "destination": "/api/index.py" } ]
}
```

**`api/index.py`**
```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.main import app  # noqa: E402  — Vercel이 이 `app`(ASGI)을 실행한다
```

**`backend/app/main.py`**
```python
from fastapi import FastAPI
from .routers import observe, decide

app = FastAPI(title="버려도 돼?")
app.include_router(observe.router, prefix="/api")
app.include_router(decide.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"ok": True}
```

**`requirements.txt`** (서버 실행용만)
```
fastapi
pydantic>=2
python-multipart
google-genai
supabase
```
**`requirements-dev.txt`**: `uvicorn[standard]`, `pytest`

**Gemini 호출 (`services/vision.py`, SDK 버전에 따라 문법이 달라질 수 있으니 공식 문서로 확인)**
```python
import os
from google import genai
from google.genai import types
from ..models import Observation

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def observe(image_bytes: bytes) -> Observation:
    resp = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            "이 사진의 쓰레기를 관찰해 JSON으로 보고하세요.",
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,      # §8.1
            response_mime_type="application/json",
            response_schema=Observation,
            temperature=0,
        ),
    )
    return resp.parsed
```

**`frontend/vite.config.ts` 프록시 (로컬 개발)**
```ts
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
```

## 부록 D. 용어
- **관찰(observation):** 사진에서 보이는 사실. AI가 만든다.
- **판단(decision):** 관찰 + 사용자 답변 + 규칙으로 계산한 결과. 규칙 엔진이 만든다.
- **경로 A/B:** 오염 제거 가능(세척·재촬영) / 불가(일반폐기물로 종료).
- **데모 모드:** `MOCK_VISION`으로 고정 관찰 응답을 쓰는 모드. 화면에 표시한다.
- **SSOT:** 단일 기준 문서(이 파일 + 디자인 이미지).
