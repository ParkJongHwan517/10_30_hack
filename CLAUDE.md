# CLAUDE.md — "버려도 돼?" 팀 공통 작업 규칙

> AI 코딩 도구가 **매 세션 시작 시** 읽는 파일이다. 짧게 유지한다.
> 제품·화면·API·규칙의 상세는 **`docs/PROJECT_SPEC.md`**(문서)와 **`docs/design-ref.png`**(디자인 이미지)가 기준이다. 이 파일은 *작업 방식(Git·코딩 규칙)* 을 다룬다.
> Cursor·Codex 등 다른 도구를 쓰는 팀원은 이 파일 내용을 그 도구의 규칙 파일(`AGENTS.md` 등)에 그대로 붙여넣는다.

---

## 1. 프로젝트 한 줄 요약

사진 한 장을 올리면 AI(Gemini)가 쓰레기의 **종류·오염·부착물·파손 상태를 관찰**하고, **부산 기준 규칙 엔진**이 배출 방법을 판단해 근거와 함께 안내하는 웹 서비스 (해커톤 18시간 MVP).

- **스택(확정):** 프론트 React + Vite + TypeScript + Tailwind / 백엔드 FastAPI(Python 3.12) + Pydantic v2 / AI **Google Gemini 비전**(`google-genai`) / DB **Supabase**(익명 로그만, 선택) / 배포 **Vercel 단일 프로젝트**(프론트 정적 + `api/index.py`)
- 패키지 매니저: 프론트 **npm**, 백엔드 **pip** (다른 것을 섞지 않는다)
- 마감: **10/31 08:30 제출**, **10/31 01:00 기능 동결**
- 팀: 5명 = **백엔드 2명 + 프론트 3명** (역할·담당 폴더는 §4. `PROJECT_SPEC.md` §14의 A~E 5역할 구분보다 **이 파일 §4가 우선**한다)
- 발표·시연(E 역할)은 별도 담당 없이 팀 전원이 나눠 맡는다.

## 2. 절대 원칙 (어기지 않는다)

1. **작업 전에 `docs/PROJECT_SPEC.md`와 `docs/design-ref.png`를 읽는다.** 문서와 이미지가 충돌하면 이미지(화면·문구)가 우선, 법적 안전 요소(§13)는 문서가 우선.
2. **AI는 관찰만, 판단은 규칙 엔진이 한다.** Gemini에게 배출 방법을 판단시키지 않는다.
3. **디자인 이미지에 없는 기능은 만들지 않는다.** 필요하면 사람에게 먼저 묻는다.
4. **API 키(`GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`)·`.env*`·사진 원본을 커밋·로그·프론트 코드(`VITE_` 변수 포함)에 넣지 않는다.**
5. **사진을 서버·DB·스토리지에 저장하지 않는다.** Supabase에는 익명 통계만 넣는다.
6. **API 형식의 원본은 `backend/app/models.py`(Pydantic).** 프론트 타입(`frontend/src/lib/api-types.ts`)은 생성 파일이며 손으로 고치지 않는다. 모델 변경은 A만 한다.
7. **분리배출 규칙·출처 URL을 지어내지 않는다.** 모르면 `UNKNOWN`으로 처리한다.
8. **Gemini 호출은 아껴 쓴다.** 5명이 같은 쿼터를 공유한다. 평소 개발은 `MOCK_VISION=true`.
9. **자기 담당 폴더만 수정한다**(§4). 공용 파일은 A만 바꾼다.
10. **`main`은 건드리지 않는다.** 모든 작업은 **내 개인 브랜치**에서 하고, 거기서 돌려본 뒤 **PR로만** `main`에 합친다(§5).
11. **파괴적 명령은 사람의 허락 없이 실행하지 않는다**(§5.9).
12. 막히거나 불확실하면 **가정을 주석·PR 설명에 적고 계속 진행**한다. 단, 충돌·공용 파일 변경은 멈추고 사람에게 알린다.

## 3. 자주 쓰는 명령

```bash
# 백엔드 (저장소 루트에서)
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000 --app-dir backend
pytest backend/tests                                    # 규칙 엔진 G1~G7 포함

# 프론트
cd frontend
npm install
npm run dev            # Vite 개발 서버 (/api 는 localhost:8000 으로 프록시)
npm run lint
npx tsc --noEmit       # 타입 검사
npm run build          # 배포 전 빌드 확인
```
- 환경변수는 **루트 `.env.local`** 에만 둔다(커밋 금지). 변수 **이름** 목록은 `.env.example`로 공유한다. 로컬 개발 기본값: `MOCK_VISION=true`.
- 가상환경(`.venv/`)과 `node_modules/`는 커밋하지 않는다.

## 4. 폴더 소유권 & 개인 브랜치 (파일 충돌 방지의 핵심)

**개인 브랜치 이름:** 백엔드 `dev/api-<이름>` / 프론트 `dev/front-<이름>` (영문 소문자, 예: `dev/api-junho`)

| 역할 (인원) | 담당자 | 담당 폴더/파일 |
|---|---|---|
| **백엔드 1 — 판독 (C)** | TODO | `backend/app/routers/observe.py`, `backend/app/services/vision.py`, `mock_vision.py`, `log.py` |
| **백엔드 2 — 규칙·데이터 (D)** | TODO | `backend/app/routers/decide.py`, `backend/app/services/decide.py`, `bullets.py`, `backend/app/rules/**`, `backend/tests/**`, `samples/**` |
| **프론트 1** | TODO | 화면 1~3 (지역 선택·촬영·AI 분석 중), `frontend/src/lib/image.ts` |
| **프론트 2** | TODO | 화면 4~5·A-6 (질문·규칙 판단·세척 안내), 보완 화면(NOTICE_RESHOOT·NOTICE_UNKNOWN·오류), 상태 머신 |
| **프론트 3** | TODO | 결과 화면(A-8/B-6/④), 공통 컴포넌트(Header·Footer·ProgressChecks·ResultCard), `frontend/src/lib/api.ts` |
| **A 통합·배포 (공용, 1명 겸임)** | TODO | `backend/app/models.py`, `backend/app/main.py`, `api/**`, `vercel.json`, `requirements*.txt`, `frontend/package*.json`, `frontend/vite.config.ts`, `frontend/src/lib/api-types.ts`(생성), `.env.example`, `.gitignore`, `docs/**`, `CLAUDE.md` — **다른 사람은 수정 전 A에게 알린다** |

- 담당자 칸(TODO)은 팀에서 정해 채운다. 프론트 화면 분담은 제안이며, 바꿔도 **같은 파일을 동시에 고치지 않는 것**만 지킨다.
- A(통합·배포)는 백엔드 2명 중 1명이 겸한다. 공용 파일은 A만 고친다.
- 남의 폴더에서 버그를 발견하면 **직접 고치지 말고 담당자에게 알리거나 PR 코멘트로 남긴다.**
- 포맷팅 일괄 적용(전체 파일 prettier/black 등), 파일 이동·이름 변경은 **충돌의 주원인**이므로 하지 않는다.

---

## 5. Git 규칙

### 5.1 브랜치 전략: `main` + 역할별 개인 브랜치

```
main  ─────●──────────●──────────────●────────  (직접 작업 금지, 항상 배포 가능, Vercel 자동 배포)
            \        / \            /
dev/front-A  ●──●──●───●──●──●──●──●            (내가 계속 쓰는 개인 브랜치)
```

- **`main` = 항상 배포 가능한 상태.** 직접 push·직접 커밋 금지(**A의 긴급 수정 제외**).
- 각자 **자기 개인 브랜치를 한 번 만들어 계속 사용**한다(작업마다 새 브랜치를 따지 않는다).
- 개인 브랜치에서 **돌려보고(로컬 + Vercel 프리뷰 URL) 동작이 확인되면 `main`에 PR로 합친다.** Vercel 프리뷰는 프론트와 백엔드가 같은 브랜치 코드로 함께 뜬다.
- 개인 브랜치는 **오래 쓰는 만큼 `main`과 벌어지기 쉬우므로**, `main`의 변경을 **자주 가져와야** 한다(§5.4).
- **다른 사람의 개인 브랜치를 내 브랜치에 합치지 않는다.** 서로의 작업은 반드시 `main`을 통해서만 주고받는다.

### 5.2 시작 루틴

**처음 한 번 (개인 브랜치 만들기)**
```bash
git checkout main
git pull origin main
git checkout -b dev/front-minsu        # 내 역할·이름으로
git push -u origin dev/front-minsu
```

**작업 세션 시작할 때마다**
```bash
git status                              # 작업 폴더가 깨끗한지 확인
git checkout dev/front-minsu
git fetch origin
git merge origin/main                   # main에 새로 들어온 변경 가져오기
```
- `main`에서 `backend/app/models.py`가 바뀌었다면 A가 `api-types.ts`를 재생성해 `main`에 올린다. 합친 뒤 프론트 타입 오류가 나면 A에게 알린다.

### 5.3 커밋 규칙

- **작게, 자주.** 의미 있는 단위로 **30~60분마다** 커밋한다. 몰아서 커밋하지 않는다.
- **커밋 메시지:** `<type>(<scope>): <한국어 요약>` (50자 안팎, 마침표 없음)

| type | 의미 | scope 예시 |
|---|---|---|
| `feat` | 기능 추가 | `front`, `api`, `vision`, `rules` |
| `fix` | 버그 수정 | |
| `test` | 테스트 | `rules` |
| `docs` | 문서 | `spec` |
| `chore` | 설정·빌드·의존성 | |
| `refactor` | 동작 변경 없는 정리 | |

예) `feat(front): 결과 화면 AI 분석 결과 불릿 추가` · `fix(api): Gemini 429 시 AI_BUSY 반환` · `test(rules): G3 경로 B 케이스 추가`

- 한 커밋에는 **한 가지 일만** 담는다.
- **커밋 전 체크 (내 담당 영역 기준)**
  - 백엔드(C·D): `pytest backend/tests`
  - 프론트(B): `npm run lint` + `npx tsc --noEmit` (큰 변경이면 `npm run build`)
  - 실패한 채로 커밋하지 않는다.
- **절대 커밋하지 않는 것:** `.env*`(`.env.example` 제외), `.venv/`, `__pycache__/`, `.pytest_cache/`, `node_modules/`, `frontend/dist/`, `.vercel/`, 키·토큰, **얼굴·송장·제품 브랜드가 보이는 사진**, 1MB를 넘는 원본 사진(`samples/`에는 리사이즈한 정리본만).

### 5.4 Pull(동기화) 규칙 — `main` → 내 개인 브랜치

```bash
git fetch origin
git merge origin/main
```

- **언제:** ① 작업 세션을 시작할 때 ② **최소 1시간마다** ③ **PR을 올리기 직전** ④ **내가 `main`에 머지한 직후** ⑤ 팀원이 `main`에 머지했다고 알렸을 때
- **rebase·force push는 쓰지 않는다.** (오래 쓰는 브랜치에서 히스토리가 꼬이는 가장 흔한 원인)
- 충돌이 나면 §5.7을 따른다.

### 5.5 Push 규칙

```bash
git push                                # 내 개인 브랜치로
```

- **내 개인 브랜치에만** push 한다. `main`에 직접 push 하지 않는다.
- **`git push --force`, `--force-with-lease` 금지.**
- 작업이 끝나지 않았더라도 **최소 1시간마다 push**해서 백업하고 진행 상황이 보이게 한다. push 하면 Vercel이 **내 브랜치 프리뷰 URL**을 만들어준다 — 여기서 실제로 돌려본다.

### 5.6 `main`에 합치기 (PR & Merge)

**합칠 타이밍:** 화면 하나·API 하나 등 **세로로 동작하는 단위가 완성되면 바로** 합친다. 몰아서 한 번에 합치지 않는다. 최소 **2~3시간마다 한 번**, 그리고 **16:30까지 첫 스켈레톤**.

**순서**
1. §5.4대로 `origin/main`을 내 브랜치에 합친다
2. 내 영역 체크 통과(§5.3)
3. **내 브랜치 프리뷰 URL(또는 로컬)에서 담당 시나리오가 동작**하는지 확인
4. GitHub에서 **`dev/...` → `main`** PR 생성(아래 템플릿)
5. 머지 규칙대로 머지
6. **머지 직후 내 브랜치에서 `git fetch origin && git merge origin/main`** 으로 다시 맞춘다

**PR 템플릿 (짧게)**
```md
## 무엇을 했나
- 

## 확인 방법
- (예: 프리뷰 URL에서 G3 시나리오 통과 / pytest 통과)

## 공용 파일 변경 여부
- 없음 / 있음(어떤 파일, 왜)

## 가정·주의
- 
```

**머지 방식: `Create a merge commit` (Squash 금지)**
- 개인 브랜치를 계속 쓰기 때문에 **Squash/Rebase merge를 쓰면 같은 변경이 다음 머지에서 다시 충돌**한다.
- **머지 후 브랜치를 삭제하지 않는다.** (GitHub의 "머지 후 브랜치 자동 삭제"는 꺼져 있어야 한다, §9)

**누가 머지하나**
- **자기 담당 폴더만** 바꾼 PR → 체크가 통과하고 **충돌이 없으면 작성자가 직접 머지**
- **공용 파일(A 영역)** 을 바꾼 PR, 또는 **다른 사람 폴더**를 건드린 PR → **A가 확인 후 머지**

**`main`이 깨졌다면**(빌드 실패·배포 오류) 모든 작업보다 우선해서 복구한다. 원인 파악이 오래 걸리면 **직전 정상 상태로 되돌린다**(§5.8).

### 5.7 충돌(Conflict) 처리 규칙

- 충돌이 나면 **추측으로 해결하지 말고 멈춘다.** 양쪽 변경의 의도를 모두 확인한다.
- **`ours`/`theirs` 일괄 선택 금지**, 충돌 표시(`<<<<<<<`)가 남은 채 커밋 금지.
- **공용 파일** 충돌은 A에게 알린다.
- **`frontend/package-lock.json` 충돌:** 내 변경을 버리고 `main`의 파일로 되돌린 뒤 `npm install`을 다시 실행해 재생성한다.
- **`requirements.txt` 충돌:** 양쪽에서 추가한 패키지를 **모두 남기고** A에게 알린다(두 줄 중 하나를 지우지 않는다).
- 충돌 해결 후 영역별 체크(`pytest` / `tsc`·`build`)를 다시 돌린다.
- 해결이 꼬였으면 `git merge --abort`로 돌아간 뒤 사람에게 알린다.

### 5.8 되돌리기

| 상황 | 방법 |
|---|---|
| 아직 커밋 안 한 내 변경 버리기 | 사람 확인 후 `git restore <파일>` |
| 내 브랜치에 push 한 커밋 되돌리기 | `git revert <커밋 해시>` (새 커밋으로 되돌림) |
| **`main`에 합쳐진 PR 되돌리기** | `main`에서 **`git revert -m 1 <머지 커밋 해시>`** (머지 커밋은 `-m 1` 필수), 그 뒤 PR로 반영 — 급하면 A가 처리 |
| 머지 중 꼬임 | `git merge --abort` |
| 그 외 | **멈추고 사람에게 알린다** |

### 5.9 금지 명령 (사람의 명시적 허락 없이는 실행 금지)

`git push --force` · `git reset --hard` · `git clean -fd` · `git checkout .` · `git rebase` · `git commit --amend`(이미 push 한 커밋) · `git branch -D` · `git push origin --delete` · `rm -rf` · 히스토리 재작성 일체 · **`main`에 직접 commit/push** · **남의 개인 브랜치 merge/push**

---

## 6. 코딩 규칙

**공통**
- **UI 문구는 한국어, `docs/design-ref.png`·`PROJECT_SPEC.md` §5.2·§12의 문구를 그대로** 쓴다. 임의로 다듬지 않는다.
- 로딩·오류 상태를 항상 처리한다(빈 화면 금지). 새 의존성은 꼭 필요할 때만 추가하고 **A에게 알린다**.
- 주석은 "왜"를 적는다. 임시 가정·TODO는 `TODO(이름):` 형식으로 남긴다.
- 외부 코드·이미지·자료를 가져오면 **출처와 라이선스**를 PR 설명에 적는다.

**백엔드 (Python)**
- 타입 힌트를 쓰고, 요청·응답은 **`backend/app/models.py`의 Pydantic 모델**을 그대로 사용한다. 비슷한 모델을 새로 만들지 않는다.
- `Tri` 값은 `"yes" | "no" | "unknown"` **문자열**이다(bool 아님).
- **규칙 엔진(`services/decide.py`)은 순수 함수**로 유지하고 AI·네트워크를 호출하지 않는다. 변경 시 **G1~G7 테스트를 먼저 통과**시킨다.
- Gemini는 **`services/vision.py`에서만** 호출한다. 이미지 바이트를 로그·응답·파일로 남기지 않는다. 타임아웃·`RESOURCE_EXHAUSTED`(429) 처리를 한다(`AI_BUSY`).
- Supabase 로그는 **실패해도 요청을 실패시키지 않는다**(1.5초 타임아웃, 예외 무시). 이미지·식별자·IP는 넣지 않는다.

**프론트 (TypeScript/React)**
- TypeScript strict, `any` 지양. API 타입은 **`api-types.ts`(생성)** 를 import 한다.
- 화면 전환은 **상태 머신(useReducer/zustand)** 으로 한다(React Router 사용 안 함).
- **모바일 우선**(폰 폭 기준). 사진은 업로드 전에 **리사이즈(긴 변 1280px) + JPEG 재인코딩**한다.
- Supabase를 프론트에서 직접 호출하지 않는다.

## 7. 한 작업의 표준 순서 (AI 도구용)

1. `docs/PROJECT_SPEC.md` 해당 절과 디자인 이미지 확인
2. `git status` → `git checkout <내 개인 브랜치>` → `git fetch origin` → `git merge origin/main`
3. 구현 (자기 폴더만) + 필요한 테스트 추가
4. 내 영역 체크 (`pytest` 또는 `lint`+`tsc`, 큰 변경이면 `build`)
5. 작은 단위로 커밋 → 1시간마다 `git push` (프리뷰 URL에서 확인)
6. 세로 단위가 완성되면: `git merge origin/main` → 체크 통과 → **`dev/... → main` PR**(템플릿) → 머지 규칙(§5.6)
7. 머지 후 **내 브랜치에서 `git fetch origin && git merge origin/main`**
8. **실제 URL에서 시나리오를 한 번 돌려본다**(코드가 도는 것 ≠ 데모 경로가 도는 것)

## 8. 일정 기반 운영 규칙

| 시점 | 규칙 |
|---|---|
| ~15:30 | A: 저장소 생성, `main` 보호, Vercel 단일 프로젝트 생성·**첫 배포 검증(`/api/health`)**, Supabase 테이블 생성, 환경변수(Production+Preview), `models.py`·`.env.example`·폴더 구조 푸시 → 팀원 clone → **각자 개인 브랜치 생성·push** |
| 16:00 | Vercel Python 배포가 안 되면 A가 Render 분리 여부 결정 |
| 16:30까지 | 모든 팀원이 **스켈레톤을 `main`에 한 번 머지**해 연결 경로를 먼저 뚫는다 |
| 매시간 | 모두 `main` 동기화(§5.4), **통합 스모크 테스트**(G1, G2→G3, G2→G4→G5, G6, G7 — 평소엔 `MOCK_VISION`) |
| **10/31 01:00** | **기능 동결.** 새 기능 PR 금지, **버그 수정만** `main`에 머지 |
| 10/31 07:30 | **`main` 동결.** A만 최종 수정 가능 |
| 10/31 08:00 | A가 최종 상태에 태그: `git tag submission-final && git push origin submission-final` |
| 10/31 08:15 | 발표자료 제출 완료 (마감 08:30) |

## 9. 저장소 초기 설정 (A가 1회)

- GitHub 저장소 생성, 팀원 전원 Collaborator 초대
- **`main` 브랜치 보호:** PR 필요, **force push 차단**, 직접 push 차단(승인 인원 수 요구는 속도 때문에 0~1명)
- **"Automatically delete head branches"(머지 후 브랜치 자동 삭제) = OFF** — 개인 브랜치를 계속 쓰기 때문
- **허용 머지 방식은 "Create a merge commit"만** 켜고, Squash·Rebase merge는 끈다
- `.gitignore`: `node_modules/`, `frontend/dist/`, `.env*`(단 `.env.example` 제외), `.venv/`, `__pycache__/`, `.pytest_cache/`, `.vercel/`, `*.log`, `.DS_Store`
- **Vercel:** 저장소 루트를 프로젝트 루트로 단일 프로젝트 연결, `main` 자동 배포, **브랜치별 프리뷰 활성화**, 환경변수(`GEMINI_API_KEY`, `GEMINI_MODEL`, `MOCK_VISION`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`)는 **대시보드에만** 입력하고 **Production과 Preview 둘 다** 설정
- **Supabase:** 프로젝트 생성 → `docs/PROJECT_SPEC.md` 부록 B의 SQL 실행 → RLS 켠 상태 유지, **service_role 키는 서버 환경변수에만**
- **Gemini:** 사용할 모델이 현재 사용 가능한지 확인하고 `GEMINI_MODEL`에 지정. 무료 티어 쿼터는 5명이 공유한다
- `docs/PROJECT_SPEC.md`, `docs/design-ref.png`, 이 파일(`CLAUDE.md`, 저장소 루트) 커밋

## 10. 모를 때 / 막혔을 때

- 규칙·화면·API 의문 → `docs/PROJECT_SPEC.md`의 해당 절을 다시 읽는다. 거기 없으면 **임의로 만들지 말고** 담당자(A)에게 묻는다.
- 20분 이상 같은 문제로 막히면 **혼자 붙잡지 말고 팀 채팅에 공유**한다(증상, 에러 메시지, 시도한 것).
