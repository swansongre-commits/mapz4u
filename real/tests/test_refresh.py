"""외부 API 호출 없이 재시도·로그 보안·전체 성공 후 저장을 검증."""
import io
import json
from pathlib import Path
import subprocess
import sys
import urllib.error

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import collect_data4library as collector
import refresh

KEY = "test-secret-key+/="


def response():
    return io.BytesIO(json.dumps({"response": {"docs": [{"doc": {
        "bookname": "book", "loan_count": "1,000"}}]}}).encode())


def http_error(code):
    return urllib.error.HTTPError("http://example.invalid?authKey=" + KEY,
                                  code, KEY, {}, io.BytesIO(KEY.encode()))


def fetch():
    return collector.fetch_band(KEY, 8, 9, "2025-10-11", "2026-10-11")


@pytest.mark.parametrize("code", [408, 429, 500, 502, 503, 504])
def test_transient_http_recovers_without_leaking_key(monkeypatch, capsys, code):
    calls, waits = [], []

    def urlopen(req, timeout):
        calls.append(req)
        assert timeout == 90
        if len(calls) == 1:
            raise http_error(code)
        return response()

    monkeypatch.setattr(collector.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(collector.time, "sleep", waits.append)
    assert fetch()[0]["loan"] == 1000
    assert len(calls) == 2 and waits == [15]
    output = capsys.readouterr().err
    assert f"HTTP_{code}" in output and "attempt=2/4" in output and "status=OK" in output
    assert KEY not in output and "authKey" not in output


def test_retry_exhaustion_uses_backoff_and_no_final_sleep(monkeypatch, capsys):
    calls, waits = [], []

    def urlopen(*args, **kwargs):
        calls.append(1)
        raise http_error(504)

    monkeypatch.setattr(collector.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(collector.time, "sleep", waits.append)
    with pytest.raises(RuntimeError, match="HTTP_504") as error:
        fetch()
    assert len(calls) == 4 and waits == [15, 30, 60]
    assert KEY not in str(error.value)
    output = capsys.readouterr().err
    assert "attempt=4/4" in output and "retry_in=0s" in output
    assert KEY not in output and "authKey" not in output


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_permanent_http_failure_does_not_retry(monkeypatch, capsys, code):
    calls, waits = [], []

    def urlopen(*args, **kwargs):
        calls.append(1)
        raise http_error(code)

    monkeypatch.setattr(collector.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(collector.time, "sleep", waits.append)
    with pytest.raises(RuntimeError, match=f"HTTP_{code}"):
        fetch()
    assert len(calls) == 1 and waits == []
    assert KEY not in capsys.readouterr().err


@pytest.mark.parametrize("error", [urllib.error.URLError(KEY), TimeoutError(KEY), ConnectionError(KEY)])
def test_network_failures_can_recover(monkeypatch, capsys, error):
    calls, waits = [], []

    def urlopen(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise error
        return response()

    monkeypatch.setattr(collector.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(collector.time, "sleep", waits.append)
    assert fetch()
    assert len(calls) == 2 and waits == [15]
    assert KEY not in capsys.readouterr().err


@pytest.mark.parametrize("payload", [b"not json", json.dumps({"response": {"error": KEY}}).encode()])
def test_invalid_response_fails_without_echoing_body(monkeypatch, capsys, payload):
    calls, waits = [], []

    def urlopen(*args, **kwargs):
        calls.append(1)
        return io.BytesIO(payload)

    monkeypatch.setattr(collector.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(collector.time, "sleep", waits.append)
    with pytest.raises(RuntimeError) as error:
        fetch()
    assert len(calls) == 1 and waits == []
    assert KEY not in str(error.value) + capsys.readouterr().err


@pytest.fixture
def output_folder(tmp_path, monkeypatch):
    (tmp_path / "state").mkdir()
    folder = tmp_path / "data/raw/data4library_api"
    folder.mkdir(parents=True)
    for band in collector.BANDS:
        (folder / f"{band}.json").write_bytes(b"old-data")
    monkeypatch.setattr(collector, "rp", lambda *parts: str(tmp_path.joinpath(*parts)))
    monkeypatch.setattr(collector, "load_env", lambda: {"DATA4LIBRARY_KEY": KEY})
    monkeypatch.setattr(collector.time, "sleep", lambda _: None)
    return folder


@pytest.mark.parametrize("failure", ["http", "short"])
def test_failed_later_band_preserves_every_existing_file(output_folder, monkeypatch, failure):
    calls = []

    def fetch_band(*args):
        calls.append(1)
        if len(calls) == 2:
            if failure == "http":
                raise RuntimeError("HTTP_504")
            return [{}] * (collector.MIN_ROWS - 1)
        return [{}] * collector.MIN_ROWS

    monkeypatch.setattr(collector, "fetch_band", fetch_band)
    with pytest.raises(SystemExit) as error:
        collector.main()
    assert error.value.code == 2 and len(calls) == 2
    assert all(p.read_bytes() == b"old-data" for p in output_folder.glob("*.json"))


def test_no_file_is_saved_until_all_bands_succeed(output_folder, monkeypatch):
    calls = []

    def fetch_band(*args):
        assert all(p.read_bytes() == b"old-data" for p in output_folder.glob("*.json"))
        calls.append(1)
        return [{}] * collector.MIN_ROWS

    monkeypatch.setattr(collector, "fetch_band", fetch_band)
    collector.main()
    assert len(calls) == 4
    for p in output_folder.glob("*.json"):
        assert len(json.loads(p.read_text(encoding="utf-8"))["rows"]) == collector.MIN_ROWS


@pytest.mark.parametrize("code", [0, 2])
def test_refresh_archives_retry_diagnostics_on_success_and_failure(tmp_path, monkeypatch, capsys, code):
    (tmp_path / "state").mkdir()
    diagnostic = "[data4library] age=8-9 attempt=1/4 elapsed=90.0s status=HTTP_504 retry_in=15s"
    monkeypatch.setattr(refresh, "rp", lambda *parts: str(tmp_path.joinpath(*parts)))
    monkeypatch.setattr(refresh, "STEPS", [("정보나루 API 수집", "unused.py")])
    monkeypatch.setattr(refresh.subprocess, "run", lambda *args, **kwargs:
                        subprocess.CompletedProcess([], code, "summary", diagnostic + "\n"))
    with pytest.raises(SystemExit) as error:
        refresh.main()
    assert error.value.code == (1 if code else 0)
    archived = (tmp_path / "state/refresh_log.md").read_text(encoding="utf-8")
    assert diagnostic in archived and diagnostic in capsys.readouterr().out
