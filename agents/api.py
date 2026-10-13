"""
FastAPI REST API Server for Spatial Transcriptomics Cell Cell Agent.
"""
from typing import Dict, Any, List, Optional
import hmac
import os
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Spatial Transcriptomics Cell Cell Agent API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)

@app.exception_handler(SecurityException)
async def _handle_phi_violation(request: Request, exc: SecurityException):
    return JSONResponse(status_code=422, content={
        "detail": "Potentially sensitive identifier detected; request rejected."
    })


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    if not os.environ.get("AUDIT_SECRET_KEY"):
        return JSONResponse(status_code=503, content={"status": "NOT_CONFIGURED", "detail": "AUDIT_SECRET_KEY required"})
    return {"status": "HEALTHY", "service": "spatial-transcriptomics-cell-cell-agent", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Audit service is not configured")
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs(authorization: Optional[str] = Header(default=None)):
    """Read-only audit export requires a dedicated bearer token.

    AUDIT_LOG_READ_TOKEN is distinct from the HMAC signing key.
    The endpoint is unavailable when this token is not configured.
    """
    expected = os.getenv("AUDIT_LOG_READ_TOKEN")
    if not expected:
        raise HTTPException(status_code=404, detail="Audit export is not enabled")
    prefix = "Bearer "
    if not authorization or not authorization.startswith(prefix) or not hmac.compare_digest(
        authorization[len(prefix):], expected
    ):
        raise HTTPException(status_code=401, detail="Unauthorized audit export")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
