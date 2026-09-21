from models.domain import APIModel, EndpointModel, FieldModel
from parsers.openapi_parser import parse_fastapi_source
from tools.analysis import build_impact_graph, calculate_quality_score, compare_versions, detect_documentation_drift


def api(version: str, extra: bool = False) -> APIModel:
    return APIModel(version=version, endpoints=[EndpointModel(method="GET", path="/items", parameters=[])], schemas={"Item": [FieldModel(name="id", type="integer")]}, auth_required=True, security_schemes=["bearer"])


def test_fastapi_parser_is_static_and_extracts_routes():
    result = parse_fastapi_source('from fastapi import FastAPI\napp=FastAPI()\n@app.get("/items")\ndef items(item_id: int):\n    return {}')
    assert result.endpoints[0].key == "GET /items"
    assert result.endpoints[0].parameters[0].name == "item_id"


def test_version_comparison_detects_removed_endpoint():
    before = APIModel(endpoints=[EndpointModel(method="GET", path="/old")])
    after = APIModel(endpoints=[])
    changes = compare_versions(before, after)
    assert changes[0].kind == "REMOVED"
    assert changes[0].severity == "HIGH"


def test_drift_radar_finds_missing_auth_and_endpoint():
    issues = detect_documentation_drift(api("2"), APIModel(endpoints=[]))
    assert any(issue.issue == "Undocumented endpoint" for issue in issues)
    assert any(issue.issue == "Authentication information is missing" for issue in issues)


def test_impact_graph_contains_field_schema_endpoint_docs():
    nodes, edges = build_impact_graph(api("1"))
    ids = {node["id"] for node in nodes}
    assert {"field:Item.id", "schema:Item", "GET /items", "docs"} <= ids
    assert any(edge["target"] == "docs" for edge in edges)


def test_quality_score_is_bounded_and_recommends_drift_fix():
    score = calculate_quality_score(api("1"), None, detect_documentation_drift(api("1"), None))
    assert 0 <= score.total <= 100
    assert score.recommendations
