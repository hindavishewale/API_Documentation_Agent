from __future__ import annotations

import json
import io
import zipfile
from pathlib import Path
import streamlit as st

from agent.graph import build_graph, source_hash
from agent.state import AgentState
from storage import KnowledgeStore

st.set_page_config(page_title="API Documentation Agent", page_icon="API", layout="wide")

st.markdown("""
<style>
:root { --ink:#17211f; --mint:#bce8d2; --coral:#f47d65; --paper:#f6f2e9; }
.stApp { background:var(--paper); color:var(--ink); }
.block-container { max-width:1400px; padding-top:2rem; }
[data-testid="stMetric"] { background:#fffdf7; border:1px solid #d7d0c3; padding:14px; border-radius:8px; }
.activity { padding:8px 12px; border-left:3px solid var(--coral); background:#fffdf7; margin:5px 0; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("API Documentation Agent")
    mode = st.radio("Input mode", ["Analyze API", "Compare V1/V2", "Check Documentation Drift", "API Knowledge Assistant"])
    uploaded = st.file_uploader("API source / OpenAPI / docs", type=["py", "yaml", "yml", "json", "md", "html", "zip"])
    v2_upload = st.file_uploader("V2 source", type=["py", "yaml", "yml", "json"], key="v2") if mode == "Compare V1/V2" else None
    request = st.text_area("Natural-language request", value={"Analyze API": "Generate documentation", "Compare V1/V2": "Compare V1 and V2", "Check Documentation Drift": "Why is my documentation outdated?", "API Knowledge Assistant": "Which endpoint requires authentication?"}[mode])
    run = st.button("Run agent", type="primary", use_container_width=True)

st.title("Self-Healing API Documentation & Change Intelligence")
st.caption("An autonomous, version-aware agent that keeps API documentation synchronized with API evolution.")

if "state" not in st.session_state:
    st.session_state.state = None
if run:
    source = None
    if uploaded:
        if uploaded.name.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(uploaded.getvalue())) as archive:
                members = [name for name in archive.namelist() if name.endswith((".py", ".yaml", ".yml", ".json")) and not name.startswith("__MACOSX/")]
                source = archive.read(members[0]).decode("utf-8", errors="replace") if members else None
        else:
            source = uploaded.getvalue().decode("utf-8", errors="replace")
    state = AgentState(request=request, api_source=source)
    if mode == "Compare V1/V2":
        if v2_upload:
            state.v1_source, state.v2_source = source, v2_upload.getvalue().decode("utf-8", errors="replace")
    graph = build_graph()
    result = graph.invoke(state)
    st.session_state.state = result if isinstance(result, AgentState) else AgentState.model_validate(result)
    KnowledgeStore().save(st.session_state.state.model_dump(), source_hash(source or ""))

state = st.session_state.state
if state:
    if state.errors:
        for error in state.errors: st.error(error)
    api = state.api
    if api:
        cols = st.columns(7)
        metrics = [("Endpoints", len(api.endpoints)), ("Schemas", len(api.schemas)), ("Parameters", sum(len(e.parameters) for e in api.endpoints)), ("Health", f"{state.quality.total}%"), ("Sync", f"{state.quality.documentation_drift}%"), ("Breaking", sum(c.severity in {'HIGH','CRITICAL'} for c in state.changes)), ("Drift", len(state.drift))]
        for col, (label, value) in zip(cols, metrics): col.metric(label, value)
        tabs = st.tabs(["Overview", "Endpoints", "Schemas", "Documentation", "OpenAPI", "Changes", "Breaking Changes", "Impact Graph", "Drift", "Security", "Quality", "Migration", "Release Notes", "Agent Activity", "API Assistant"])
        with tabs[0]: st.subheader("Analysis overview"); st.write("The analysis is grounded in static source/OpenAPI facts. Gemini is optional and only used for semantic explanations.")
        with tabs[1]: st.dataframe([e.model_dump() for e in api.endpoints], use_container_width=True)
        with tabs[2]: st.json({name: [f.model_dump() for f in fields] for name, fields in api.schemas.items()})
        with tabs[3]: st.download_button("Download Markdown", state.artifacts.get("documentation.md", ""), file_name="documentation.md"); st.markdown(state.artifacts.get("documentation.md", ""))
        with tabs[4]: st.download_button("Download OpenAPI YAML", state.artifacts.get("openapi.yaml", ""), file_name="openapi.yaml"); st.code(state.artifacts.get("openapi.yaml", ""), language="yaml")
        with tabs[5]: st.dataframe([c.model_dump() for c in state.changes], use_container_width=True)
        with tabs[6]: st.dataframe([c.model_dump() for c in state.changes if c.severity in {"HIGH", "CRITICAL"}], use_container_width=True)
        with tabs[7]:
            st.graphviz_chart("digraph { rankdir=LR; " + " ".join(f'"{e["source"]}" -> "{e["target"]}";' for e in state.impact_edges) + " }")
        with tabs[8]: st.dataframe([d.model_dump() for d in state.drift], use_container_width=True)
        with tabs[9]: st.write({"Detected schemes": api.security_schemes, "Documentation consistency": "Review drift report"})
        with tabs[10]: st.json(state.quality.model_dump())
        with tabs[11]: st.markdown(state.artifacts.get("migration-guide.md", ""))
        with tabs[12]: st.markdown(state.artifacts.get("release-notes.md", ""))
        with tabs[13]: st.markdown("\n".join(f"<div class='activity'>✓ {item}</div>" for item in state.activity), unsafe_allow_html=True)
        with tabs[14]:
            question = st.text_input("Ask about the analyzed API")
            if question:
                st.info("Answers are restricted to the structured analysis. " + ("Relevant facts are available in the tables above." if api else "Analyze an API first."))
        st.download_button("Download complete analysis JSON", json.dumps(state.model_dump(), indent=2, default=str), file_name="analysis.json")
else:
    st.info("Upload a FastAPI source file or OpenAPI 3.x document, choose an input mode, and run the agent.")
