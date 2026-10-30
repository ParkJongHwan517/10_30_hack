import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.main import app  # noqa: E402,F401  — Vercel이 이 `app`(ASGI)을 실행한다
