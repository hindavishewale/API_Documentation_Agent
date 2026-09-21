from __future__ import annotations

from typing import Any
from models.domain import APIChange, APIModel, DriftIssue, QualityScore


def _endpoint_map(api: APIModel) -> dict[str, Any]:
    return {endpoint.key: endpoint for endpoint in api.endpoints}


def compare_versions(before: APIModel, after: APIModel) -> list[APIChange]:
    old, new = _endpoint_map(before), _endpoint_map(after)
    changes: list[APIChange] = []
    for key in sorted(set(old) | set(new)):
        if key not in old:
            changes.append(APIChange(kind="ADDED", component=key, after=new[key].model_dump(),
                reason="Endpoint is present only in the newer API.", consumer_impact="New capability; existing consumers are unaffected.", recommended_action="Document and publish the endpoint."))
        elif key not in new:
            changes.append(APIChange(kind="REMOVED", component=key, before=old[key].model_dump(), severity="HIGH",
                reason="Endpoint no longer exists in the newer API.", consumer_impact="Consumers calling this endpoint will fail.", recommended_action="Provide a replacement and migration timeline."))
        elif old[key].model_dump() == new[key].model_dump():
            changes.append(APIChange(kind="UNCHANGED", component=key))
        else:
            changes.append(APIChange(kind="MODIFIED", component=key, before=old[key].model_dump(), after=new[key].model_dump(),
                severity="MEDIUM", reason="Endpoint contract changed.", consumer_impact="Consumers may need to update requests or response handling.", recommended_action="Review the field-level diff and update clients."))
    for name in sorted(set(before.schemas) | set(after.schemas)):
        if name in before.schemas and name in after.schemas:
            old_fields = {field.name: field for field in before.schemas[name]}
            new_fields = {field.name: field for field in after.schemas[name]}
            for field in sorted(set(old_fields) | set(new_fields)):
                if field not in new_fields:
                    changes.append(APIChange(kind="MODIFIED", component=f"schema:{name}.{field}", before=old_fields[field].model_dump(), severity="HIGH",
                        reason="Response or request field was removed.", consumer_impact="Consumers reading this field may break.", recommended_action="Migrate consumers before removal."))
                elif field not in old_fields:
                    severity = "HIGH" if new_fields[field].required else "MEDIUM"
                    changes.append(APIChange(kind="MODIFIED", component=f"schema:{name}.{field}", after=new_fields[field].model_dump(), severity=severity,
                        reason="Field was added to the schema.", consumer_impact="Required fields can break existing requests." if severity == "HIGH" else "Optional field is additive.", recommended_action="Add the field to requests when required."))
                elif old_fields[field].type != new_fields[field].type:
                    changes.append(APIChange(kind="MODIFIED", component=f"schema:{name}.{field}", severity="HIGH",
                        reason="Field data type changed.", consumer_impact="Serialization and validation may fail for consumers.", recommended_action="Update client models and migration code."))
    return changes


def detect_documentation_drift(api: APIModel, documented: APIModel | None) -> list[DriftIssue]:
    if documented is None:
        return [DriftIssue(severity="CRITICAL", issue="Documentation was not provided.", component="API", documentation_section="Overview", recommendation="Generate documentation from the analyzed API.")]
    actual, docs = _endpoint_map(api), _endpoint_map(documented)
    issues: list[DriftIssue] = []
    for key in sorted(set(actual) - set(docs)):
        issues.append(DriftIssue(severity="HIGH", issue="Undocumented endpoint", component=key, documentation_section=f"Endpoint {key}", recommendation="Add the endpoint to the documentation."))
    for key in sorted(set(docs) - set(actual)):
        issues.append(DriftIssue(severity="CRITICAL", issue="Deleted endpoint still documented", component=key, documentation_section=f"Endpoint {key}", recommendation="Remove or mark the endpoint deprecated."))
    for key in sorted(set(actual) & set(docs)):
        if {p.name for p in actual[key].parameters} != {p.name for p in docs[key].parameters}:
            issues.append(DriftIssue(severity="HIGH", issue="Parameter list is outdated", component=key, documentation_section=f"Endpoint {key} parameters", recommendation="Regenerate the parameter section."))
        if {f.name for f in actual[key].response_fields} != {f.name for f in docs[key].response_fields}:
            issues.append(DriftIssue(severity="HIGH", issue="Response schema is outdated", component=key, documentation_section=f"Endpoint {key} response", recommendation="Update response fields and examples."))
    if api.auth_required and not documented.auth_required:
        issues.append(DriftIssue(severity="HIGH", issue="Authentication information is missing", component="security", documentation_section="Authentication", recommendation="Document the detected security scheme."))
    return issues


def calculate_quality_score(api: APIModel, documented: APIModel | None, drift: list[DriftIssue]) -> QualityScore:
    total_endpoints = len(api.endpoints) or 1
    documented_keys = set(_endpoint_map(documented)) if documented else set()
    endpoint_coverage = round(100 * len(set(_endpoint_map(api)) & documented_keys) / total_endpoints)
    parameter_coverage = round(100 * sum(bool(e.parameters) for e in api.endpoints) / total_endpoints)
    schema_coverage = round(100 * len(api.schemas) / max(1, len(api.schemas)))
    auth = 100 if not api.auth_required or documented and documented.auth_required else 0
    drift_score = max(0, 100 - sum({"CRITICAL": 30, "HIGH": 20, "MEDIUM": 10, "LOW": 3}[i.severity] for i in drift))
    values = dict(endpoint_coverage=endpoint_coverage, parameter_coverage=parameter_coverage, schema_coverage=schema_coverage,
                  request_example_coverage=0, response_example_coverage=0, error_documentation=0,
                  authentication_documentation=auth, consistency=drift_score, openapi_validity=100, documentation_drift=drift_score)
    total = round(sum(values.values()) / len(values))
    recommendations = []
    if endpoint_coverage < 100: recommendations.append("Document every detected endpoint.")
    if drift: recommendations.append("Resolve documentation drift before publishing.")
    if auth == 0: recommendations.append("Add authentication requirements to the security section.")
    return QualityScore(**values, total=total, recommendations=recommendations)


def build_impact_graph(api: APIModel, changes: list[APIChange] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    nodes, edges = [], []
    for schema, fields in api.schemas.items():
        schema_id = f"schema:{schema}"; nodes.append({"id": schema_id, "label": schema, "type": "schema"})
        for field in fields:
            field_id = f"field:{schema}.{field.name}"; nodes.append({"id": field_id, "label": field.name, "type": "field"}); edges.append({"source": field_id, "target": schema_id})
    for endpoint in api.endpoints:
        endpoint_id = endpoint.key; nodes.append({"id": endpoint_id, "label": endpoint_id, "type": "endpoint"})
        for schema in api.schemas:
            if any(field.name in {f.name for f in endpoint.request_fields + endpoint.response_fields} for field in api.schemas[schema]):
                edges.append({"source": f"schema:{schema}", "target": endpoint_id})
        edges.append({"source": endpoint_id, "target": "docs"})
    nodes.append({"id": "docs", "label": "API Documentation", "type": "documentation"})
    changed = {change.component for change in (changes or [])}
    for node in nodes:
        node["changed"] = node["id"] in changed or node["label"] in changed
    return nodes, edges
