"""시연 사진 정답표(samples/expected.json)로 실제 Gemini 판독 + 규칙 결과를 채점한다. pytest 대상 아님.

    # 배포된 서버로 (Vercel에 설정된 모델 사용)
    python backend/tests/eval_samples.py --url https://<배포-URL>
    # 로컬에서 모델 비교 (.env.local의 GEMINI_API_KEY 사용)
    python backend/tests/eval_samples.py --local --models gemini-3.1-flash-lite,gemini-3.5-flash-lite

- 실제 Gemini를 사진 수 × 모델 수만큼 부른다(무료 키 공유 쿼터). 호출 수를 먼저 보여주고 --yes가 있어야 실행한다.
- 사진이 크면 macOS sips로 긴 변 1280px JPEG 사본을 임시로 만들어 보낸다(프론트 리사이즈와 같은 조건).
- 규칙 판단은 항상 로컬 코드(services.decide)로 한다 → 배포 모델과 현재 규칙의 조합을 본다.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import Observation  # noqa: E402
from app.services.decide import decide, photo_gate_reason  # noqa: E402

SAMPLES = ROOT / "samples"
REGION = {"sido": "부산광역시", "gu": "해운대구"}
MAX_EDGE, MAX_BYTES = 1280, 1_000_000


def outcome(o: Observation) -> str:
    d = decide(o, REGION, None, 1)
    return d.result_code if d.kind == "FINAL" else d.kind


def prepare(path: Path, tmp: Path) -> bytes:
    """프론트와 같은 조건(긴 변 1280px JPEG)으로 맞춘 바이트."""
    if path.stat().st_size <= MAX_BYTES and path.suffix.lower() in (".jpg", ".jpeg"):
        return path.read_bytes()
    if not shutil.which("sips"):
        sys.exit(f"{path.name}: 1MB 초과·비JPEG인데 sips가 없어요. 1280px JPEG로 줄여서 넣어 주세요.")
    out = tmp / (path.stem + ".jpg")
    subprocess.run(
        ["sips", "-Z", str(MAX_EDGE), "-s", "format", "jpeg", "-s", "formatOptions", "80", str(path), "--out", str(out)],
        check=True, capture_output=True,
    )
    return out.read_bytes()


def load_env_local() -> None:
    env = ROOT / ".env.local"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def observe_url(base: str, data: bytes) -> list[Observation]:
    import httpx

    r = httpx.post(f"{base.rstrip('/')}/api/observe", files={"image": ("s.jpg", data, "image/jpeg")}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code} {r.text[:120]}")
    body = r.json()
    if body.get("demo_mode"):
        raise RuntimeError("배포가 데모 모드(MOCK_VISION=true)라 실제 판독이 아니에요")
    return [Observation.model_validate(o) for o in (body.get("items") or [body["observation"]])]


def observe_local(model: str, data: bytes) -> list[Observation]:
    from app.services import vision

    os.environ["GEMINI_MODEL"] = model
    return vision.observe(data, "image/jpeg")


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="배포 URL (Vercel의 GEMINI_MODEL 사용)")
    g.add_argument("--local", action="store_true", help="로컬에서 직접 Gemini 호출 (.env.local)")
    ap.add_argument("--models", default="gemini-3.1-flash-lite", help="--local일 때 쉼표로 구분")
    ap.add_argument("--only", help="이 문자열이 파일명에 들어간 사진만")
    ap.add_argument("--yes", action="store_true", help="쿼터 사용 확인")
    args = ap.parse_args()

    spec = json.loads((SAMPLES / "expected.json").read_text(encoding="utf-8"))["samples"]
    cases = [s for s in spec if (SAMPLES / s["file"]).exists() and (not args.only or args.only in s["file"])]
    missing = [s["file"] for s in spec if not (SAMPLES / s["file"]).exists()]
    if missing:
        print(f"사진 없음(건너뜀): {', '.join(missing)}")
    if not cases:
        print("채점할 사진이 없어요. samples/에 사진을 넣어 주세요.")
        return 1

    runs = [("배포", None)] if args.url else [(m, m) for m in args.models.split(",")]
    calls = len(cases) * len(runs)
    print(f"Gemini 호출 {calls}번 예정 (사진 {len(cases)} × {'배포 모델' if args.url else f'모델 {len(runs)}개'})")
    if not args.yes:
        print("쿼터를 쓰니 확인 후 --yes를 붙여 다시 실행하세요.")
        return 0
    if args.local:
        load_env_local()
        if not os.getenv("GEMINI_API_KEY"):
            sys.exit(".env.local에 GEMINI_API_KEY가 필요해요.")

    summary = []
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        images = {s["file"]: prepare(SAMPLES / s["file"], tmp) for s in cases}
        for label, model in runs:
            print(f"\n=== {label} ===")
            main_ok = full_ok = 0
            times = []
            for s in cases:
                t0 = time.perf_counter()
                try:
                    items = observe_url(args.url, images[s["file"]]) if args.url else observe_local(model, images[s["file"]])
                except Exception as e:  # noqa: BLE001 — 한 장 실패해도 나머지는 채점
                    print(f"❌ {s['file']}: 오류 {e}")
                    continue
                ms = int((time.perf_counter() - t0) * 1000)
                times.append(ms)
                gate = photo_gate_reason(items)
                got = [f"RESHOOT_QUALITY({gate})"] if gate else [outcome(o) for o in items]
                m_ok = bool(got) and got[0] == s["expect"][0]
                f_ok = sorted(got) == sorted(s["expect"])
                main_ok += m_ok
                full_ok += f_ok
                seen = ", ".join(f"{o.label_ko or o.item_type}/{o.material_guess}" for o in items)
                mark = "✅" if f_ok else ("🟡" if m_ok else "❌")
                print(f"{mark} {s['file']:<22} {ms:>6}ms  기대 {s['expect']}  결과 {got}  ({seen})")
            n = len(cases)
            summary.append((label, main_ok, full_ok, n, times))

    print("\n=== 요약 (✅ 전체 일치 · 🟡 대표 항목만 일치) ===")
    for label, m, f, n, times in summary:
        tm = f"평균 {sum(times) // len(times)}ms · 최대 {max(times)}ms" if times else "-"
        print(f"{label:<28} 대표 {m}/{n} · 전체 {f}/{n} · {tm}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
