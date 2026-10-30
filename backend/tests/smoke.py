"""배포 URL 스모크 테스트 (PROJECT_SPEC §15). pytest가 아니라 직접 실행한다.

    python backend/tests/smoke.py https://<배포-URL> [--image 사진.jpg]

- /api/health, /api/decide 골든 시나리오(G1, G2→G3, G2→G4→G5, G6, G7)를 끝까지 돌린다.
- --image를 주면 /api/observe도 1회 호출한다. 실제 Gemini 모드면 쿼터를 쓰므로 필요할 때만.
- 결과 문구가 아니라 흐름(kind·result_code)과 검증 표시만 본다. 문구는 pytest가 본다.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

FIXTURES = Path(__file__).parent / "fixtures"
REGION = {"sido": "부산광역시", "gu": "해운대구"}


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--image", help="JPEG 경로 (주면 /api/observe 호출)")
    args = ap.parse_args()
    base = args.url.rstrip("/")
    client = httpx.Client(timeout=40)
    failures = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        failures += not ok
        print(f"{'✅' if ok else '❌'} {label}{'  ' + detail if detail else ''}")

    def decide(obs: str, attempt: int = 1, answer: str | None = None) -> dict:
        body = {"region": REGION, "observation": fixture(obs), "attempt": attempt, "demo_mode": True}
        if answer:
            body["answers"] = {"contamination_removable": answer}
        t = time.perf_counter()
        r = client.post(f"{base}/api/decide", json=body)
        r.raise_for_status()
        d = r.json()
        d["_ms"] = int((time.perf_counter() - t) * 1000)
        return d

    try:
        r = client.get(f"{base}/api/health")
        check("health", r.status_code == 200 and r.json().get("ok") is True, str(r.status_code))

        scenarios = [
            ("G1 투명 페트병", [("pet_clear_label", 1, None, "FINAL", "PET_CLEAR")]),
            ("G2→G3 경로 B", [
                ("styrofoam_sauce", 1, None, "ASK_QUESTION", None),
                ("styrofoam_sauce", 1, "no", "FINAL", "GENERAL"),
            ]),
            ("G2→G4→G5 경로 A", [
                ("styrofoam_sauce", 1, "yes", "WASH_AND_RESHOOT", None),
                ("styrofoam_clean", 2, None, "FINAL", "STYROFOAM"),
            ]),
            ("G6 플라스틱", [("plastic_pp_clean", 1, None, "FINAL", "PLASTIC")]),
            ("G7 종이상자", [("cardboard_tape", 1, None, "FINAL", "PAPER")]),
            ("G8 캔", [("can_empty", 1, None, "FINAL", "CAN")]),
            ("G9 비닐", [("vinyl_clean", 1, None, "FINAL", "VINYL")]),
            ("G10 유리병", [("glass_bottle_empty", 1, None, "FINAL", "GLASS")]),
            ("G11 종이팩", [("paper_pack_milk", 1, None, "FINAL", "PAPER_PACK")]),
        ]
        last = None
        for label, steps in scenarios:
            got = []
            ok = True
            for obs, attempt, answer, kind, code in steps:
                d = decide(obs, attempt, answer)
                got.append(f"{d['kind']}/{d.get('result_code')} {d['_ms']}ms")
                ok &= d["kind"] == kind and d.get("result_code") == code
                last = d
            check(label, ok, " → ".join(got))

        if last:
            check(
                "검증 표시",
                last["rules_verified"] and last["basis_label"] == "부산광역시 2026년 기준" and bool(last["source"]["url"]),
                f"{last['basis_label']} / {last['source']['url']}",
            )

        if args.image:
            t = time.perf_counter()
            r = client.post(
                f"{base}/api/observe",
                files={"image": ("smoke.jpg", Path(args.image).read_bytes(), "image/jpeg")},
            )
            ms = int((time.perf_counter() - t) * 1000)
            if r.status_code == 200:
                o = r.json()
                check("observe", True, f"{ms}ms demo_mode={o['demo_mode']} ok={o['ok']} item={o['observation']['item_type']}")
            else:
                check("observe", False, f"{r.status_code} {ms}ms {r.text[:200]}")
    except httpx.HTTPError as e:
        check("요청 실패", False, repr(e))

    print(f"\n{'모두 통과' if failures == 0 else f'실패 {failures}건'} — {base}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
