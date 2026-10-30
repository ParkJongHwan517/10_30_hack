import sys
from pathlib import Path

# 저장소 루트에서 `pytest backend/tests`로 실행해도 `app` 패키지를 찾도록 backend/를 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
