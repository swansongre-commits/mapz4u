#!/usr/bin/env python3
"""
preflight_check.py — MAPZ_AUTOPILOT.md 실행 전 사전점검 스크립트

목적: AUTOPILOT을 무인으로 돌리기 전에, 실행에 필요한 것들이 갖춰져 있는지
      한 번에 점검하고 결과를 보여준다. 문제를 고치는 게 아니라 "무엇이
      부족한지, 부족해도 어떤 모드로 대체되는지"를 알려주는 게 목적이다.

사용법:
    python preflight_check.py
    (mapz 프로젝트 루트에서 실행. 아직 mapz 폴더가 없어도 실행 가능 —
     그 경우 "폴더 없음, Phase 0에서 자동 생성됨"으로 안내한다.)
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# ── 결과 수집 ────────────────────────────────────────────────
results = []  # (구분, 항목, 상태, 메모)  상태: "OK" | "대체가능" | "부족"


def check(category, name, ok, note="", fallback=None):
    if ok:
        status = "OK"
    elif fallback:
        status = "대체가능"
        note = f"{note} → {fallback}" if note else fallback
    else:
        status = "부족"
    results.append((category, name, status, note))


# ── 1. Python 버전 ───────────────────────────────────────────
py_ver = sys.version_info
check(
    "환경",
    "Python 버전",
    py_ver >= (3, 10),
    note=f"현재 {py_ver.major}.{py_ver.minor}.{py_ver.micro}",
)

# ── 2. venv 생성 가능 여부 ───────────────────────────────────
venv_ok = importlib.util.find_spec("venv") is not None
check("환경", "venv 모듈", venv_ok, note="Python 표준 라이브러리")

# ── 3. pip 사용 가능 여부 ────────────────────────────────────
pip_ok = shutil.which("pip") is not None or shutil.which("pip3") is not None
check("환경", "pip", pip_ok)

# ── 4. git ────────────────────────────────────────────────────
git_ok = shutil.which("git") is not None
check("환경", "git", git_ok, note="없으면 커밋 이력 없이 진행 가능(권장하지 않음)")

# ── 5. 네트워크 연결 ─────────────────────────────────────────
def has_network(url="https://www.google.com", timeout=3):
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False


network_ok = has_network()
check(
    "환경",
    "네트워크 연결",
    network_ok,
    note="오프라인" if not network_ok else "",
    fallback="EMBED_TIER=3(TF-IDF), MODE=SEED로 전환" if not network_ok else None,
)

# ── 6. GPU 감지 (선택 사항) ──────────────────────────────────
def has_gpu():
    try:
        subprocess.run(
            ["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        return True
    except Exception:
        return False


gpu_ok = has_gpu()
check(
    "환경",
    "GPU (nvidia-smi)",
    gpu_ok,
    note="GPU 없음" if not gpu_ok else "",
    fallback="EMBED_TIER=2(경량 모델) 또는 3(TF-IDF)로 자동 전환" if not gpu_ok else None,
)

# ── 7. 프로젝트 필수 문서 존재 ───────────────────────────────
root = Path.cwd()
required_docs = {
    "MAPZ_기획방향_실행계획.md": True,   # 필수
    "MAPZ_AUTOPILOT.md": True,           # 필수
    "MAPZ_ASSET_MANIFEST.md": False,     # 선택 — 없으면 MAPS_ASSETS=FALSE로 진행
}
for fname, required in required_docs.items():
    exists = (root / fname).exists()
    if required:
        check("문서", fname, exists)
    else:
        check(
            "문서",
            fname,
            exists,
            note="없음" if not exists else "",
            fallback="MAPS_ASSETS=FALSE로 진행 (직업·학과 데이터 자체 생성)"
            if not exists
            else None,
        )

# ── 8. .env 키 점검 ──────────────────────────────────────────
env_path = root / ".env"
env_vars = {}
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env_vars[k.strip()] = v.strip()

check("문서", ".env 파일", env_path.exists(), fallback="MODE=SEED로 진행" if not env_path.exists() else None)

for key, desc in [
    ("DATA_GO_KR_KEY", "공공데이터포털 인증키 (문화정보원 API용)"),
    ("DATA4LIBRARY_KEY", "정보나루 인증키 (도서 데이터용)"),
]:
    val = env_vars.get(key, "")
    present = bool(val) and val.upper() not in ("", "YOUR_KEY_HERE", "TODO")
    check(
        "키",
        f"{key} ({desc})",
        present,
        note="비어있음/미설정" if not present else "",
        fallback="해당 소스는 NOKEY/SEED 경로로 대체" if not present else None,
    )

# ── 9. 필수 파이썬 패키지 설치 가능 여부 (실제 설치는 안 함, import 테스트만) ──
core_packages = ["fastapi", "uvicorn", "jinja2", "requests", "bs4", "pandas", "sklearn", "pytest", "httpx"]
optional_packages = ["sentence_transformers", "faiss", "playwright"]

for pkg in core_packages:
    installed = importlib.util.find_spec(pkg) is not None
    check(
        "패키지(필수)",
        pkg,
        installed,
        note="미설치" if not installed else "",
        fallback="requirements.txt로 설치 예정 (Phase 0에서 자동 설치)" if not installed else None,
    )

for pkg in optional_packages:
    installed = importlib.util.find_spec(pkg) is not None
    check(
        "패키지(선택)",
        pkg,
        installed,
        note="미설치" if not installed else "",
        fallback="폴백 경로로 자동 대체 (EMBED_TIER/스크린샷 SKIP 등)" if not installed else None,
    )

# ── 10. 디스크 여유 공간 ─────────────────────────────────────
try:
    total, used, free = shutil.disk_usage(root)
    free_gb = free / (1024**3)
    check("환경", "디스크 여유공간", free_gb >= 2, note=f"{free_gb:.1f}GB 남음")
except Exception:
    check("환경", "디스크 여유공간", False, note="확인 실패")

# ── 결과 출력 ────────────────────────────────────────────────
print("=" * 60)
print("MAPZ AUTOPILOT 사전점검 결과")
print("=" * 60)

cur_cat = None
counts = {"OK": 0, "대체가능": 0, "부족": 0}
blocking = []

for cat, name, status, note in results:
    if cat != cur_cat:
        print(f"\n[{cat}]")
        cur_cat = cat
    mark = {"OK": "✅", "대체가능": "🟡", "부족": "❌"}[status]
    line = f"  {mark} {name}"
    if note:
        line += f"  — {note}"
    print(line)
    counts[status] += 1
    if status == "부족" and cat == "문서" and name in ("MAPZ_기획방향_실행계획.md", "MAPZ_AUTOPILOT.md"):
        blocking.append(name)
    if status == "부족" and cat == "환경" and name in ("Python 버전", "venv 모듈", "pip"):
        blocking.append(name)

print("\n" + "=" * 60)
print(f"요약: OK {counts['OK']}건 / 대체가능 {counts['대체가능']}건 / 부족 {counts['부족']}건")
print("=" * 60)

if blocking:
    print("\n🚫 실행 불가 — 아래 항목은 대체 경로가 없어 먼저 해결해야 합니다:")
    for b in blocking:
        print(f"   - {b}")
    sys.exit(1)
elif counts["부족"] > 0:
    print("\n🟡 실행 가능 — 일부 항목이 부족하지만 AUTOPILOT이 자동으로 대체 경로(SEED/NOKEY/폴백)로 진행합니다.")
    sys.exit(0)
else:
    print("\n✅ 실행 가능 — 모든 항목이 준비되었습니다. MODE=API로 최대한 실데이터를 사용해 진행됩니다.")
    sys.exit(0)
