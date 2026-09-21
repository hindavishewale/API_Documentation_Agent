from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from generators.artifacts import api_to_openapi, generate_markdown
from models.domain import APIChange, APIModel, DriftIssue
from tools.analysis import build_impact_graph, calculate_quality_score, compare_versions, detect_documentation_drift

class SecurityCheck(BaseModel):
    issues: list[DriftIssue] = Field(default_factory=list)
    detected_schemes: list[str] = Field(default_factory=list)

class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    score: int = 0


def extract_schemas(api: APIModel) -> dict[str, Any]:
    return {name: [field.model_dump() for field in fields] for name, fields in api.schemas.items()}


def analyze_api(api: APIModel) -> dict[str, Any]:
    return {"endpoints": len(api.endpoints), "schemas": len(api.schemas), "parameters": sum(len(endpoint.parameters) for endpoint in api.endpoints), "security_schemes": api.security_schemes}


def generate_openapi(api: APIModel) -> dict[str, Any]:
    return api_to_openapi(api)


def generate_docs(api: APIModel) -> str:
    return generate_markdown(api)


def validate_docs(api: APIModel, documented: APIModel | None = None) -> ValidationResult:
    drift = detect_documentation_drift(api, documented)
    score = calculate_quality_score(api, documented, drift).total
    return ValidationResult(valid=not any(issue.severity in {"CRITICAL", "HIGH"} for issue in drift), errors=[issue.issue for issue in drift], score=score)


def detect_breaking_changes(before: APIModel, after: APIModel) -> list[APIChange]:
    return [change for change in compare_versions(before, after) if change.severity in {"CRITICAL", "HIGH"}]


def analyze_impact(api: APIModel, changes: list[APIChange]) -> dict[str, Any]:
    nodes, edges = build_impact_graph(api, changes)
    return {"nodes": nodes, "edges": edges, "changed_components": [change.component for change in changes if change.severity in {"CRITICAL", "HIGH"}]}


def map_changes_to_docs(changes: list[APIChange]) -> list[APIChange]:
    sections = {"schema": ["schema", "response", "request", "example"], "GET ": ["endpoint", "response", "example"], "POST ": ["endpoint", "request", "response", "example"]}
    for change in changes:
        change.affected_docs = next((value for key, value in sections.items() if change.component.startswith(key) or change.component.startswith(key)), ["API reference", "migration guide"])
    return changes


def security_documentation_check(api: APIModel, documented: APIModel | None) -> SecurityCheck:
    if not api.auth_required or documented and documented.auth_required:
        return SecurityCheck(detected_schemes=api.security_schemes)
    return SecurityCheck(detected_schemes=api.security_schemes, issues=[DriftIssue(severity="HIGH", issue="Authentication section missing", component="security", documentation_section="Authentication", recommendation="Document the detected authentication requirement.")])


def self_heal_documentation(api: APIModel, documented: APIModel | None = None, max_retries: int = 3) -> dict[str, Any]:
    history = []
    current = documented
    for attempt in range(max_retries + 1):
        result = validate_docs(api, current)
        history.append({"attempt": attempt, "score": result.score, "errors": result.errors})
        if result.valid or attempt == max_retries:
            return {"documentation": generate_docs(api), "history": history, "retries": attempt, "final": result.model_dump()}
        current = api
    return {"documentation": generate_docs(api), "history": history, "retries": max_retries}


def generate_migration_guide(changes: list[APIChange]) -> str:
    from generators.artifacts import migration_guide
    return migration_guide(map_changes_to_docs(changes))


def generate_release_notes(changes: list[APIChange]) -> str:
    from generators.artifacts import release_notes
    return release_notes(changes)


def answer_api_question(question: str, api: APIModel) -> str:
    question_lower = question.lower()
    if "auth" in question_lower:
        return ", ".join(api.security_schemes) if api.security_schemes else "Not specified in source."
    if "endpoint" in question_lower or "creates" in question_lower:
        matches = [endpoint.key for endpoint in api.endpoints if "post" in question_lower and endpoint.method == "POST"]
        return ", ".join(matches) if matches else "; ".join(endpoint.key for endpoint in api.endpoints)
    return "The requested fact is not specified in the analyzed API."
