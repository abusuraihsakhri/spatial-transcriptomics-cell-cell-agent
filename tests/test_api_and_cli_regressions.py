import json
from fastapi.testclient import TestClient
from agents.api import app
from agents.base import AuditLogger, AuditTrail
from spatial_cell_comm.cli import main as spatial_main


def test_api_configuration_and_audit_export(monkeypatch):
    AuditLogger.reset()
    monkeypatch.delenv("AUDIT_SECRET_KEY", raising=False)
    monkeypatch.delenv("AUDIT_LOG_READ_TOKEN", raising=False)
    client = TestClient(app)
    assert client.get("/health").status_code == 503
    payload = {
        "task_id": "S1", "target_identifier": "KEY-01",
        "primary_metric": 1.0, "secondary_metric": 1.0
    }
    assert client.post("/api/audit", json=payload).status_code == 503
    assert client.get("/api/audit/logs").status_code == 404
    monkeypatch.setenv("AUDIT_SECRET_KEY", "test-key-for-audit-tests-only")
    monkeypatch.setenv("AUDIT_LOG_READ_TOKEN", "test-read-token-keep-private")
    assert client.get("/health").status_code == 200
    assert client.post("/api/audit", json=payload).status_code == 200
    assert client.get("/api/audit/logs").status_code == 401
    assert client.get("/api/audit/logs", headers={"Authorization": "Bearer incorrect"}).status_code == 401
    response = client.get("/api/audit/logs", headers={"Authorization": "Bearer test-read-token-keep-private"})
    assert response.status_code == 200
    assert response.json()["verified"] is True


def test_api_phi_rejection_does_not_expose_identifier(monkeypatch):
    monkeypatch.setenv("AUDIT_SECRET_KEY", "test-key-for-audit-tests-only")
    client = TestClient(app)
    payload = {"task_id": "MRN-123456", "target_identifier": "KEY", "primary_metric": 1}
    response = client.post("/api/audit", json=payload)
    assert response.status_code == 422
    assert "123456" not in response.text


def test_audit_export_is_defensive_copy():
    trail = AuditTrail(secret_key="local-unit-test-key-123")
    trail.log("test", "tier", "EVALUATED", {"status": "OK"})
    snapshot = trail.get_trail()
    snapshot[0]["payload_hash"] = "modified"
    assert trail.verify_integrity() is True


def test_spatial_cli_proximity(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "input.csv").write_text("cell_id,cell_type,x,y\n1,T,0,0\n2,M,3,4\n", encoding="utf-8")
    assert spatial_main(["proximity", "-i", "input.csv", "--radius", "5", "-o", "result.json"]) == 0
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert result["n_pairs"] == 1
    assert spatial_main(["proximity", "-i", "input.csv", "--radius", "0"]) == 1
    assert spatial_main(["proximity", "-i", "input.csv", "--radius", "5", "-o", "input.csv"]) == 1
