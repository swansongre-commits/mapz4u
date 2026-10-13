"""운영 날짜 환경변수와 한국시간 자정 경계 회귀 검증."""
import ast
import datetime
import importlib.util
import os
from pathlib import Path
import sqlite3
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import main

RealDateTime = datetime.datetime


@pytest.fixture
def clock(monkeypatch):
    class Clock(RealDateTime):
        instant = RealDateTime.fromisoformat("2026-10-11T15:00:00+00:00")

        @classmethod
        def now(cls, tz=None):
            assert tz == main.KST
            return cls.instant.astimezone(tz)

    monkeypatch.setattr(datetime, "datetime", Clock)
    monkeypatch.setenv("MAPZ_RUN_DATE", "2026-07-04")
    return Clock


def test_operating_dates_ignore_old_environment(clock):
    assert main.today() == "2026-10-12"
    spec = importlib.util.spec_from_file_location("date_common_for_test", ROOT / "scripts/common.py")
    common = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(common)
    assert common.TODAY.isoformat() == "2026-10-12"

    # UI 초기화나 관리자 DB 동작 없이 실제 날짜 계산 코드만 실행한다.
    namespace = {"datetime": datetime, "os": os, "KST": main.KST}
    admin_tree = ast.parse((ROOT / "admin/admin_app.py").read_text(encoding="utf-8"))
    today_fn = next(n for n in admin_tree.body if isinstance(n, ast.FunctionDef) and n.name == "today")
    exec(compile(ast.Module(body=[today_fn], type_ignores=[]), "admin_date", "exec"), namespace)
    assert namespace["today"]() == "2026-10-12"
    streamlit_tree = ast.parse((ROOT / "streamlit_app.py").read_text(encoding="utf-8"))
    date_assignments = [n for n in streamlit_tree.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id in {"RUN_DATE", "TODAY"}
                                for t in n.targets)]
    exec(compile(ast.Module(body=date_assignments, type_ignores=[]), "streamlit_date", "exec"), namespace)
    assert namespace["TODAY"] == "2026-10-12"


def test_request_date_changes_at_korean_midnight(clock):
    client = TestClient(main.app)
    clock.instant = RealDateTime.fromisoformat("2026-10-11T14:59:59+00:00")
    assert client.get("/healthz").json()["today"] == "2026-10-11"
    clock.instant = RealDateTime.fromisoformat("2026-10-11T15:00:00+00:00")
    assert client.get("/healthz").json()["today"] == "2026-10-12"


def test_old_environment_cannot_expose_expired_events(clock, tmp_path, monkeypatch):
    # 매일 바뀌는 데이터에 의존하지 않도록 만료·당일 종료 사례를 임시 DB에 준비.
    test_db = tmp_path / "dates.db"
    with sqlite3.connect(Path(main.DB).as_uri() + "?mode=ro", uri=True) as source:
        with sqlite3.connect(test_db) as target:
            source.backup(target)
            ids = [r[0] for r in target.execute("SELECT id FROM experience LIMIT 2")]
            target.execute("UPDATE experience SET status='운영중', period_end=? WHERE id=?",
                           ("2026-10-11", ids[0]))
            target.execute("UPDATE experience SET status='운영중', period_end=? WHERE id=?",
                           ("2026-10-12", ids[1]))
    monkeypatch.setattr(main, "DB", str(test_db))
    with sqlite3.connect(Path(main.DB).as_uri() + "?mode=ro", uri=True) as con:
        expired = {r[0] for r in con.execute(
            "SELECT id FROM experience WHERE status='운영중' AND period_end!='' AND period_end < ?",
            ("2026-10-12",))}
        eligible = con.execute(f"SELECT COUNT(*) FROM experience WHERE {main.FRESH}",
                               ("2026-10-12",)).fetchone()[0]
    assert expired  # 실제로 필터링할 만료 자료가 있는 테스트 데이터.
    client = TestClient(main.app)
    result = client.get("/api/map").json()
    assert result["today"] == "2026-10-12"
    assert result["count"] == eligible
    assert not (expired & {x["id"] for x in result["markers"]})
    assert ids[1] in {x["id"] for x in result["markers"]}  # 종료일 당일까지는 노출.
    result = client.get("/api/search").json()
    assert result["today"] == "2026-10-12"
    assert result["count"] == eligible
    assert not (expired & {x["id"] for x in result["results"]})
