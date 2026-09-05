# Spatial Transcriptomics Cell Cell Agent

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Spatial Transcriptomics Cell Cell Agent** is an advanced analytical and computational platform implementing 10x Visium Delaunay mesh & CellChat ligand-receptor communication hub agent.

The system provides a multi-worker evaluation engine that processes task payloads through specialized workers (InvariantQC, SafetyEscalation, ProtocolConformance) to produce consensus dossiers with cryptographic audit trails.

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization with automated clinical/operational action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection.
- **Multi-Worker Architecture**: Specialized workers for QC, safety, and protocol conformance evaluation.
- **HMAC-SHA256 Audit Trail**: Cryptographically tamper-evident logging with chain verification.
- **PHI Outbound Guard**: Regex-based detection and blocking of protected health information.

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/spatial-transcriptomics-cell-cell-agent.git
cd spatial-transcriptomics-cell-cell-agent

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## 💻 CLI Usage

### 1. Run Single Audit Evaluation
```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Query Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch FastAPI REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--task-id` | Unique task/case identifier | `TASK-2026-001` |
| `--target` | Entity or target identifier | `KEY-TARGET-01` |
| `--primary` | Primary measurement (float) | `28.5` |
| `--secondary` | Secondary measurement (float) | `14.2` |
| `--critical` | Emergency escalation flag | `False` |
| `--status` | Status/phenotype descriptor | `DISCORDANT` |

---

## 🌐 REST API Endpoints

When running the server (`python cli.py serve`), the following endpoints are available:

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/health` | Health and metadata check |
| `GET` | `/metrics` | Operational metrics (dossier count, audit blocks) |
| `POST` | `/api/audit` | Dispatch task payload across workers |
| `POST` | `/api/chat` | Supervisory conversational assistant |
| `GET` | `/api/audit/logs` | Retrieve and verify HMAC audit trail |

### Example API Request
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-001",
    "target_identifier": "TARGET-01",
    "primary_metric": 28.5,
    "secondary_metric": 14.2,
    "status_descriptor": "DISCORDANT",
    "is_critical_flag": true
  }'
```

---

## 🔐 Security Configuration

### Required Environment Variable

**`AUDIT_SECRET_KEY`** must be set before running the application. This key is used for HMAC-SHA256 audit trail signing.

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-cryptographically-random-key-min-16-chars"

# Windows (PowerShell)
$env:AUDIT_SECRET_KEY="your-cryptographically-random-key-min-16-chars"

# Windows (CMD)
set AUDIT_SECRET_KEY=your-cryptographically-random-key-min-16-chars
```

> ⚠️ **Security Warning**: Never use hardcoded secrets in production. Generate a cryptographically random key of at least 32 characters.

### Docker Deployment

Create a `.env` file:
```env
AUDIT_SECRET_KEY=your-production-audit-key-here
MODEL_PROVIDER=mock
```

Then run:
```bash
docker-compose up --build
```

---

## 🧪 Testing & Verification

### Run the automated test suite:
```bash
# Set test key
export AUDIT_SECRET_KEY="test-audit-key-for-unit-tests-2026"

# Run tests
pytest -v
```

### Run simulation benchmark:
```bash
python simulator.py 1000
```

---

## 🛡️ Security Features

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs with full signature verification.
* **Input Validation:** Finite number checks (NaN/Infinity rejection), path traversal prevention, and identifier sanitization.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 📁 Project Structure

```
spatial-transcriptomics-cell-cell-agent/
├── agents/                    # Core agent modules
│   ├── __init__.py           # Package init
│   ├── api.py                # FastAPI REST server
│   ├── base.py               # Security, PHI guard, audit trail
│   ├── learning.py           # Bayesian calibration engine
│   ├── llm_factory.py        # LLM provider factory
│   ├── metrics.py            # Prometheus metrics collector
│   ├── models.py             # Pydantic data schemas
│   ├── streamer.py           # WebSocket telemetry broadcaster
│   ├── supervisor.py         # Supervisor orchestrator
│   └── workers.py            # Specialized worker agents
├── spatial_cell_comm/         # SpatialCellComm sub-package
│   ├── __init__.py
│   ├── agents.py             # Spatial agent implementations
│   ├── cli.py                # Spatial CLI
│   ├── engine.py             # Core algorithmic engine
│   ├── models.py             # Data models
│   └── server.py             # Spatial FastAPI server
├── tests/                     # Test suite
│   ├── test_enrichment.py
│   ├── test_spatial_cell_comm.py
│   └── test_spatial_transcriptomics_cell_cell_agent.py
├── web/                       # Web dashboard
│   └── index.html
├── .github/workflows/         # CI/CD
│   └── ci.yml
├── cli.py                     # Main CLI entry point
├── simulator.py               # Simulation benchmark
├── enrichment.py              # Enrichment features
├── pyproject.toml             # Project metadata
├── Dockerfile                 # Docker build
├── docker-compose.yml         # Docker Compose config
└── README.md                  # This file
```

---

## 🐳 Container Deployment

```bash
docker build -t spatial-transcriptomics-cell-cell-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key spatial-transcriptomics-cell-cell-agent
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
