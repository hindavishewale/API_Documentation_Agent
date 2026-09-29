from __future__ import annotations

import hashlib
import os
from typing import Any
from dotenv import load_dotenv
from agent.planner import plan_tools
from agent.state import AgentState
from generators.artifacts import api_to_openapi, generate_html, generate_markdown, migration_guide, release_notes, report_markdown
from parsers.openapi_parser import parse_api
from tools.analysis import build_impact_graph, calculate_quality_score, compare_versions, detect_documentation_drift
from tools.toolkit import map_changes_to_docs, self_heal_documentation

load_dotenv()


def _get_gemini_key() -> str | None:
    """Load GEMINI_API_KEY from st.secrets (Streamlit Cloud) or .env (local)."""
    try:
        import streamlit as st
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY")


def _gemini_explain(prompt: str) -> str | None:
    api_key = _get_gemini_key()
    if not api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception:
        return None


def run_agent(state: AgentState) -> AgentState:
    tools = plan_tools(state.request)
    state.activity.append(f"Tool plan selected: {' -> '.join(tools)}")
    try:
        if state.api_source:
            state.api = parse_api(source=state.api_source)
            state.activity += ["Input analyzed", "FastAPI/OpenAPI parser selected", f"{len(state.api.endpoints)} endpoints detected", "Schema extraction completed"]
        if state.documented_source:
            state.documented_api = parse_api(source=state.documented_source)
        if state.v1_source and state.v2_source:
            before, after = parse_api(source=state.v1_source), parse_api(source=state.v2_source)
            state.api = after
            state.changes = compare_versions(before, after)
            state.changes = map_changes_to_docs(state.changes)
            state.activity.append(f"{sum(c.severity in {'HIGH', 'CRITICAL'} for c in state.changes)} breaking changes detected")
        if state.api and ("detect_documentation_drift" in tools or state.documented_api):
            state.drift = detect_documentation_drift(state.api, state.documented_api)
        if state.api:
            state.quality = calculate_quality_score(state.api, state.documented_api, state.drift)
            state.impact_nodes, state.impact_edges = build_impact_graph(state.api, state.changes)
            openapi = api_to_openapi(state.api)
            markdown = generate_markdown(state.api, state.quality)
            state.artifacts = {
                "documentation.md": markdown,
                "documentation.html": generate_html(markdown),
                "openapi.json": __import__("json").dumps(openapi, indent=2),
                "openapi.yaml": __import__("yaml").safe_dump(openapi, sort_keys=False),
                "quality-report.md": report_markdown("Documentation Quality Report", [state.quality]),
                "drift-report.md": report_markdown("Documentation Drift Report", state.drift),
                "change-report.md": report_markdown("API Change Report", state.changes),
                "migration-guide.md": migration_guide(state.changes),
                "release-notes.md": release_notes(state.changes),
            }
            healing = self_heal_documentation(state.api, state.documented_api)
            state.artifacts["self-healing-report.json"] = __import__("json").dumps(healing, indent=2)
            state.activity.append(f"Self-healing validation completed in {healing['retries']} retries")
            state.activity += ["Documentation generated", "Validation completed", "Impact analysis completed"]
        if state.request and not state.api and "answer_api_question" in tools:
            state.errors.append("Analyze an API before asking questions.")
    except Exception as exc:
        state.errors.append(str(exc))
    return state


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def build_graph() -> Any:
    try:
        from langgraph.graph import END, StateGraph
        graph = StateGraph(AgentState)
        graph.add_node("agent", run_agent)
        graph.set_entry_point("agent")
        graph.add_edge("agent", END)
        return graph.compile()
    except ImportError:
        return type("LocalGraph", (), {"invoke": staticmethod(lambda state: run_agent(AgentState.model_validate(state)))})()
