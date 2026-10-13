# Spatial Transcriptomics Cell–Cell Agent

A **descriptive cell-type spatial proximity** tool for 2D cell/spot coordinates. The standalone browser app runs locally without transmitting input records. A Python CLI implements the same proximity definition. Legacy generic audit interfaces remain available separately.

## Spatial analysis

Input: CSV with exactly these required columns (additional columns are allowed):

| Column | Meaning |
| --- | --- |
| cell_id | Unique cell or spot identifier |
| cell_type | Categorical cell/spot type |
| x, y | Finite coordinates in one consistent unit (for example, µm) |

Every pair of **distinct** cells/spots at Euclidean distance **≤ radius** contributes one unordered pair of cell types (A–B equals B–A). Same-type pairs are included. The table reports each observed pair count and mean distance; the summary reports cells, cell types and all nearby pairs.

### Browser workflow

Open the published Pages app, or open [web/index.html](web/index.html) locally in a modern browser. Load a CSV file or paste records, select a radius, analyze, inspect the scatterplot and pair table, and download a CSV summary. The example is loaded automatically.

Files are processed **entirely in the browser** using JavaScript; there are no API calls. Selected files are limited to 2 MB and analysis to 3,000 cells/spots. Avoid using identifiable patient data.

### Python workflow

Install Python 3.9+ and run:

    python -m pip install -e .
    spatial-cell-comm proximity -i sample_spatial.csv --radius 5 -o proximity.json

Or from the checkout without installing an entry point:

    python -m spatial_cell_comm.cli proximity -i sample_spatial.csv --radius 5

The Python proximity implementation handles up to 5,000 rows by default, rejects empty/duplicate IDs, invalid coordinates and invalid radius, and writes JSON to stdout or the requested output file. CLI input and output paths must resolve under the working directory.

**Scientific limits:** The proximity counts are descriptive, not inferential. They are **not** measurements of ligand–receptor activity, CellChat signaling, directional communication, or statistical enrichment. Delaunay triangulation and gene-expression analysis are not implemented. Upstream cell-type annotation, physical coordinate calibration and appropriate biological controls remain necessary. Do not treat observed colocalization as evidence of direct signaling.

## Legacy audit CLI and API

The existing numerical audit programs are retained for compatibility but remain **generic example threshold evaluators**, not validated spatial-omics analyses or clinical decision support. They check supplied metrics and status text against built-in arbitrary rules.

    python -m pip install -e ".[api]"
    export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
    python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2
    python cli.py batch -i sample.csv -o results.csv
    python cli.py chat "What is the status?"
    python cli.py verify-audit
    python cli.py serve --host 127.0.0.1 --port 8000

The API provides GET /health, GET /metrics, POST /api/audit and POST /api/chat. GET /api/audit/logs is disabled by default; setting a separate AUDIT_LOG_READ_TOKEN enables read-only access with Authorization: Bearer TOKEN. Do not reuse the HMAC signing key for that token.

AUDIT_SECRET_KEY must be configured for audit operations. Use a random key of at least 32 bytes (minimum implementation length: 16 characters). Audit chains are **process-memory only**, not persistent audit storage. The regex-based PHI guard cannot guarantee de-identification or HIPAA compliance. The LLM adapter is a deterministic mock; remote and local model provider integrations are not implemented.

Docker Compose binds the Python API to 127.0.0.1:8000 by default and requires AUDIT_SECRET_KEY. Do not expose the unauthenticated task submission endpoints to untrusted networks.

## Development and verification

    python -m pip install -e ".[api,test]"
    export AUDIT_SECRET_KEY=unit-test-placeholder-key
    pytest -q
    node --check web/app.js
    node --test tests/test_proximity_web.cjs

Node.js is used only for browser-unit testing, not by the production browser app. CI runs the Python tests and browser JavaScript tests. The Pages workflow publishes web/ when GitHub Pages is configured to deploy from GitHub Actions.

The frontend uses standard JavaScript, File APIs and Canvas and is intended for recent Chrome, Firefox, Edge and Safari; exhaustive cross-browser coverage has not been performed.

## Repository contents

- [web/](web/): standalone browser spatial-proximity app
- [spatial_cell_comm/proximity.py](spatial_cell_comm/proximity.py): Python proximity algorithm
- [spatial_cell_comm/cli.py](spatial_cell_comm/cli.py): spatial CLI and retained generic audit tools
- [agents/](agents/), [cli.py](cli.py): legacy generic audit backend, REST API, and CLI
- [tests/](tests/): Python and Node.js regression tests
- [.github/workflows/](.github/workflows/): CI and Pages deployment

## License

MIT — see [LICENSE](LICENSE).
