from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
ChangeKind = Literal["ADDED", "REMOVED", "MODIFIED", "UNCHANGED"]


class ParameterModel(BaseModel):
    name: str
    location: str = "query"
    required: bool = False
    type: str = "unknown"
    description: str = "Not specified in source."


class FieldModel(BaseModel):
    name: str
    type: str = "unknown"
    required: bool = False
    description: str = "Not specified in source."


class EndpointModel(BaseModel):
    method: str
    path: str
    summary: str = "Not specified in source."
    description: str = "Not specified in source."
    parameters: list[ParameterModel] = Field(default_factory=list)
    request_fields: list[FieldModel] = Field(default_factory=list)
    response_fields: list[FieldModel] = Field(default_factory=list)
    status_codes: list[str] = Field(default_factory=list)
    auth: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    examples: dict[str, Any] = Field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.method.upper()} {self.path}"


class APIModel(BaseModel):
    title: str = "API"
    version: str = "0.0.0"
    source_type: str = "openapi"
    endpoints: list[EndpointModel] = Field(default_factory=list)
    schemas: dict[str, list[FieldModel]] = Field(default_factory=dict)
    security_schemes: list[str] = Field(default_factory=list)
    auth_required: bool = False


class APIChange(BaseModel):
    kind: ChangeKind
    component: str
    before: Any = None
    after: Any = None
    severity: Severity = "LOW"
    reason: str = ""
    consumer_impact: str = ""
    recommended_action: str = ""
    affected_docs: list[str] = Field(default_factory=list)


class DriftIssue(BaseModel):
    severity: Severity
    issue: str
    component: str
    documentation_section: str
    recommendation: str


class QualityScore(BaseModel):
    endpoint_coverage: int = 0
    parameter_coverage: int = 0
    schema_coverage: int = 0
    request_example_coverage: int = 0
    response_example_coverage: int = 0
    error_documentation: int = 0
    authentication_documentation: int = 0
    consistency: int = 0
    openapi_validity: int = 0
    documentation_drift: int = 0
    total: int = 0
    recommendations: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    api: APIModel
    quality: QualityScore = Field(default_factory=QualityScore)
    drift: list[DriftIssue] = Field(default_factory=list)
    changes: list[APIChange] = Field(default_factory=list)
    impact_nodes: list[dict[str, Any]] = Field(default_factory=list)
    impact_edges: list[dict[str, str]] = Field(default_factory=list)
    activity: list[str] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
