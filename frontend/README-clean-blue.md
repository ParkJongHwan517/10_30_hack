# 버려도 돼? — Clean Blue 프론트엔드

이 작업물은 `frontend/` 경로에 덮어씌울 소스 파일만 포함합니다. `src/lib/api-types.ts`는 기존 생성 파일을 그대로 사용하며 이 압축 파일에는 포함하지 않습니다.

## 구현 범위

- `REGION → CAMERA → OBSERVING → QUESTION / RULE_LOOKUP → WASH_GUIDE / RESULT` 상태 머신
- 흐림·개인정보 노출 재촬영 안내 및 UNKNOWN 안내
- `/api/observe` multipart 업로드와 `/api/decide` JSON 요청
- 결과 화면은 `Decision` 응답의 `basis_label`, `headline`, `analysis_bullets`, `steps`, `source` 값을 문구 변경 없이 표시
- 1280px 리사이즈 및 JPEG 재인코딩으로 EXIF 제거
- 로컬 테스트: `?fixture=styrofoam_sauce`, `?fixture=pet_clear_label`, `?fixture=plastic_pp_clean`, `?fixture=cardboard_tape`
  - fixture는 `backend/tests/fixtures/*.json` 파일을 `?raw`로 직접 읽습니다.
  - `?fixture=styrofoam_sauce`에서 세척 후 재촬영 시 `styrofoam_clean.json`을 선택합니다.
  - fixture mode는 Vite 개발 서버에서만 동작하고, `/api/decide`는 실제 백엔드에 요청합니다.

## 실행

저장소 루트에서 백엔드를 실행합니다.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
MOCK_VISION=true uvicorn app.main:app --reload --port 8000 --app-dir backend
```

별도 터미널에서 프론트엔드를 실행합니다.

```bash
cd frontend
npm install
npm run dev
npm run lint
npx tsc --noEmit
npm run build
```

## API 연결

- 기본 API 주소는 같은 origin의 `/api`입니다.
- 백엔드가 별도 호스트에 있을 때만 루트 `.env.local`에 `VITE_API_BASE`를 설정합니다.
- API 키는 프론트엔드에 두지 않습니다.
- `api-types.ts`는 생성 파일이므로 직접 수정하지 않습니다.

## 참고

GitHub 권한 오류와 이 세션의 네트워크 DNS 제한으로 원격 브랜치 `HY`에 push하지 못했습니다. 이 파일들은 `frontend/`에 적용한 뒤 개인 브랜치에서 lint/type/build를 확인하고 PR로 올려야 합니다.
