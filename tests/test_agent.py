from agent.planner import plan_tools
from agent.graph import run_agent
from agent.state import AgentState


def test_planner_selects_compare_pipeline():
    tools = plan_tools("Compare V1 and V2 and generate migration guide")
    assert "compare_versions" in tools
    assert "detect_breaking_changes" in tools
    assert "parse_documentation" not in tools


def test_agent_generates_downloadable_artifacts():
    state = run_agent(AgentState(request="Generate documentation", api_source='from fastapi import FastAPI\napp=FastAPI()\n@app.get("/health")\ndef health():\n    return {"ok": True}'))
    assert "documentation.md" in state.artifacts
    assert "openapi.yaml" in state.artifacts
    assert state.quality.total >= 0
