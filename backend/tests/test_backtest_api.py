from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_mock_backtest_api_loop_returns_status_logs_and_result() -> None:
    client = TestClient(app)
    request = {
        "strategy_version_id": "strategy-version-1",
        "instruments": ["000001.SZ"],
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "resolution": "daily",
        "adjustment": "qfq",
        "initial_capital": "100000.00",
        "base_currency": "CNY",
        "benchmark": "000300.SH",
        "parameters": [{"name": "fast", "value": 5}, {"name": "slow", "value": 20}],
        "commission_model": "mock",
        "slippage_model": "mock",
        "data_snapshot_id": "snapshot-1",
    }

    submit_response = client.post(
        "/backtests/mock",
        json=request,
        headers={"X-Trace-ID": "trace-backtest"},
    )

    assert submit_response.status_code == 200
    submitted = submit_response.json()
    assert submitted["status"] == "accepted"
    assert submitted["trace_id"] == "trace-backtest"
    job_id = submitted["job_id"]
    assert job_id

    status_response = client.get(f"/jobs/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["state"] == "succeeded"
    assert status_response.json()["progress_percent"] == 100

    logs_response = client.get(f"/jobs/{job_id}/logs")
    assert logs_response.status_code == 200
    log_messages = [entry["message"] for entry in logs_response.json()["entries"]]
    assert "mock backtest succeeded" in log_messages

    result_response = client.get(f"/backtests/mock/{job_id}/result")
    assert result_response.status_code == 200
    result = result_response.json()
    assert result["job_id"] == job_id
    assert result["artifact_uri"] == "memory://mock-backtest/result"
    assert result["trade_count"] == 4


def test_cancel_completed_mock_backtest_returns_validation_error() -> None:
    client = TestClient(app)
    request = {
        "strategy_version_id": "strategy-version-2",
        "instruments": ["000001.SZ"],
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "resolution": "daily",
        "adjustment": "qfq",
        "initial_capital": "100000.00",
        "base_currency": "CNY",
        "benchmark": "000300.SH",
        "parameters": [],
        "commission_model": "mock",
        "slippage_model": "mock",
        "data_snapshot_id": "snapshot-1",
    }
    job_id = client.post("/backtests/mock", json=request).json()["job_id"]

    response = client.post(f"/jobs/{job_id}/cancel")

    assert response.status_code == 409
    assert response.json()["code"] == "VALIDATION_ERROR"
