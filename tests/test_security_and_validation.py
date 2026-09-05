"""
Security and Input Validation Tests for Spatial Transcriptomics Cell Cell Agent.
Tests for path traversal protection, NaN/Infinity validation, and audit key requirements.
"""
import os
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set a test audit key before importing agents
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-for-unit-tests-2026")

import pytest
from agents.base import PHIGuard, AuditLogger, AuditTrail, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel


@pytest.fixture(autouse=True)
def _preserve_audit_env():
    """Ensure AUDIT_SECRET_KEY is preserved across tests."""
    original = os.environ.get("AUDIT_SECRET_KEY")
    yield
    # Restore the original value after each test
    if original is None:
        os.environ.pop("AUDIT_SECRET_KEY", None)
    else:
        os.environ["AUDIT_SECRET_KEY"] = original
    # Reset the global audit singleton so each test gets a fresh trail
    AuditLogger.reset()


class TestAuditKeyValidation:
    """Tests for AUDIT_SECRET_KEY requirement."""

    def test_audit_trail_requires_key(self, _preserve_audit_env):
        """AuditTrail should raise RuntimeError when no key is provided."""
        os.environ.pop("AUDIT_SECRET_KEY", None)
        with pytest.raises(RuntimeError, match="AUDIT_SECRET_KEY"):
            AuditTrail()

    def test_audit_trail_rejects_short_key(self, _preserve_audit_env):
        """AuditTrail should reject keys shorter than 16 characters."""
        with pytest.raises(ValueError, match="at least 16 characters"):
            AuditTrail(secret_key="short")

    def test_audit_trail_accepts_valid_key(self, _preserve_audit_env):
        """AuditTrail should accept keys of 16+ characters."""
        trail = AuditTrail(secret_key="valid-test-key-16ch")
        assert trail is not None

    def test_audit_trail_uses_env_var(self, _preserve_audit_env):
        """AuditTrail should use AUDIT_SECRET_KEY from environment."""
        os.environ["AUDIT_SECRET_KEY"] = "env-based-test-key-16ch"
        trail = AuditTrail()
        assert trail is not None


class TestAuditIntegrityVerification:
    """Tests for HMAC-SHA256 audit trail integrity verification."""

    def test_verify_integrity_with_valid_chain(self):
        """Audit trail with valid entries should pass integrity check."""
        AuditLogger.reset()
        trail = AuditTrail(secret_key="test-integrity-key-16ch")
        trail.log("test", "tier", "EVENT", {"data": "value1"})
        trail.log("test", "tier", "EVENT", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_verify_integrity_detects_tampering(self):
        """Tampered audit entries should fail integrity check."""
        AuditLogger.reset()
        trail = AuditTrail(secret_key="test-integrity-key-16ch")
        trail.log("test", "tier", "EVENT", {"data": "original"})
        # Tamper with the entry
        trail.logs[0]["payload_hash"] = "tampered_hash"
        assert trail.verify_integrity() is False

    def test_verify_integrity_detects_chain_break(self):
        """Broken chain linkage should fail integrity check."""
        AuditLogger.reset()
        trail = AuditTrail(secret_key="test-integrity-key-16ch")
        trail.log("test", "tier", "EVENT", {"data": "value1"})
        trail.log("test", "tier", "EVENT", {"data": "value2"})
        # Break the chain
        trail.logs[1]["prev_hash"] = "broken_link"
        assert trail.verify_integrity() is False


class TestInputValidation:
    """Tests for SystemTaskPayload input validation."""

    def test_reject_nan_primary_metric(self):
        """NaN primary_metric should be rejected."""
        with pytest.raises(ValueError, match="finite"):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=float("nan"))

    def test_reject_inf_primary_metric(self):
        """Infinity primary_metric should be rejected."""
        with pytest.raises(ValueError, match="finite"):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=float("inf"))

    def test_reject_negative_inf_secondary_metric(self):
        """Negative infinity secondary_metric should be rejected."""
        with pytest.raises(ValueError, match="finite"):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=1.0, secondary_metric=float("-inf"))

    def test_reject_path_traversal_in_task_id(self):
        """Path traversal characters in task_id should be rejected."""
        with pytest.raises(ValueError, match="path traversal"):
            SystemTaskPayload(task_id="../etc/passwd", target_identifier="K1", primary_metric=1.0)

    def test_reject_path_traversal_in_target(self):
        """Path traversal characters in target_identifier should be rejected."""
        with pytest.raises(ValueError, match="path traversal"):
            SystemTaskPayload(task_id="T1", target_identifier="..\\windows\\system32", primary_metric=1.0)

    def test_reject_empty_task_id(self):
        """Empty task_id should be rejected."""
        with pytest.raises(ValueError):
            SystemTaskPayload(task_id="", target_identifier="K1", primary_metric=1.0)

    def test_accept_valid_payload(self):
        """Valid payload should be accepted."""
        p = SystemTaskPayload(task_id="TASK-001", target_identifier="TARGET-01", primary_metric=25.0, secondary_metric=10.0)
        assert p.task_id == "TASK-001"
        assert p.primary_metric == 25.0


class TestPHIGuardEnhanced:
    """Enhanced tests for PHI guard functionality."""

    def test_redact_phi_preserves_structure(self):
        """PHI redaction should preserve non-PHI text."""
        text = "Patient MRN-12345 visited clinic. Result: normal."
        redacted = PHIGuard.redact_phi(text)
        assert "REDACTED_IDENTIFIER" in redacted
        assert "visited clinic" in redacted
        assert "Result: normal" in redacted

    def test_clean_text_passes(self):
        """Clean text without PHI should pass."""
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")

    def test_ssn_pattern_detected(self):
        """SSN pattern should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_pattern_detected(self):
        """Phone number pattern should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_email_pattern_detected(self):
        """Email pattern should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")
