from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    request: str = ""
    api_source: str | None = None
    documented_source: str | None = None
    v1_source: str | None = None
    v2_source: str | None = None
    api: Any = None
    documented_api: Any = None
    changes: list[Any] = Field(default_factory=list)
    drift: list[Any] = Field(default_factory=list)
    quality: Any = None
    impact_nodes: list[dict[str, Any]] = Field(default_factory=list)
    impact_edges: list[dict[str, str]] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
    activity: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    rag_used: bool = False
