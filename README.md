# API Documentation Agent

## Self-Healing API Documentation & Change Intelligence Platform

API Documentation Agent is an autonomous, version-aware documentation system for FastAPI and OpenAPI 3.x. It maintains synchronization between API source and documentation through deterministic parsing, change intelligence, drift detection, impact reasoning, bounded self-correction, and structured API knowledge memory.

This is deliberately not a generic chatbot, API test runner, or penetration-testing product. Its core loop is:

`API code -> understand -> document -> validate -> detect changes -> detect drift -> predict impact -> update documentation`

## Why it is different

Traditional generators create a snapshot. This agent compares actual API contracts with existing documentation, classifies drift, maps changes to exact documentation sections, predicts consumer impact, builds an impact graph, and produces migration/release artifacts. Uploaded Python is parsed with `ast`; it is never imported or executed.

## Features

- Static FastAPI AST and OpenAPI 3.x parsing
- Documentation Drift Radar with CRITICAL/HIGH/MEDIUM/LOW issues and sync scoring
- Normalized V1/V2 endpoint and schema comparison
- Breaking-change classification and consumer actions
- API impact graph from fields to schemas to endpoints to documentation
- Documentation health score and recommendations
- Self-healing artifact workflow with a maximum of three retries
- SQLite structured knowledge memory
- Optional Gemini 2.5 Flash semantic reasoning through `google-genai`
- Optional Sentence Transformers + FAISS RAG context retrieval
- Markdown, HTML, OpenAPI YAML/JSON, reports, migration guide, release notes, and JSON downloads
- Streamlit dashboard with safe high-level agent activity only

## Architecture

- `parsers/`: deterministic AST/OpenAPI normalization
- `models/`: Pydantic contracts for all analysis data
- `tools/`: comparison, drift, scoring, and graph analysis
- `generators/`: validated artifact rendering
- `agent/`: intent-based planning and bounded LangGraph execution
- `storage.py`: SQLite knowledge base
- `rag/`: optional standards retrieval
- `app.py`: Streamlit dashboard

## Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Set `GEMINI_API_KEY` in `.env` only when semantic explanation or generation is needed. Deterministic extraction does not require a key. The app never executes uploaded source or makes arbitrary external calls.

## Demonstration

Use `sample_apis/v1/main.py` and `sample_apis/v2/main.py` to demonstrate added `/orders`, removed `DELETE /products/{product_id}`, changed path parameter types, newly required schema fields, and authentication changes. The generated outputs show the change report, breaking changes, impact graph, drift findings, update recommendations, migration guide, and release notes.

## Tests

```powershell
pytest -q
```

The suite covers static parsing, schema extraction, comparison, breaking severity, drift radar, impact graph, quality scoring, planner routing, and artifact generation.

## Inputs and outputs

Inputs include FastAPI Python, OpenAPI YAML/JSON, pasted code, existing Markdown/HTML/OpenAPI documentation, V1/V2 pairs, and natural-language requests. Outputs are available as dashboard downloads and include documentation, OpenAPI, quality, drift, changes, breaking changes, impact analysis, update plan data, security consistency findings, migration guide, and release notes.

## Limitations and future scope

The AST parser intentionally focuses on common FastAPI decorator patterns and cannot infer runtime-generated routes. HTML and Markdown ingestion is contract-oriented and should be extended with richer section parsers for unusual layouts. Future work can add file watchers, CI checks, vector-index persistence, richer schema reference resolution, and pull-request documentation patches.
