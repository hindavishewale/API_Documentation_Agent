from __future__ import annotations

import json
from typing import Any
import yaml
from models.domain import APIModel, APIChange, DriftIssue, QualityScore


def api_to_openapi(api: APIModel) -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for endpoint in api.endpoints:
        operation = {"summary": endpoint.summary, "description": endpoint.description, "responses": {code: {"description": "Not specified in source."} for code in (endpoint.status_codes or ["200"])}}
        if endpoint.parameters:
            operation["parameters"] = [{"name": p.name, "in": p.location, "required": p.required, "schema": {"type": p.type}} for p in endpoint.parameters]
        paths.setdefault(endpoint.path, {})[endpoint.method.lower()] = operation
    return {"openapi": "3.0.3", "info": {"title": api.title, "version": api.version}, "paths": paths,
            "components": {"schemas": {name: {"type": "object", "properties": {f.name: {"type": f.type} for f in fields}, "required": [f.name for f in fields if f.required]} for name, fields in api.schemas.items()},
                            "securitySchemes": {name: {"type": "http", "scheme": "bearer"} for name in api.security_schemes}}}


def generate_markdown(api: APIModel, quality: QualityScore | None = None) -> str:
    lines = [f"# {api.title}", "", f"Version: `{api.version}`", "", "## Endpoints", ""]
    for endpoint in api.endpoints:
        lines += [f"### `{endpoint.method} {endpoint.path}`", endpoint.summary, "", "**Parameters**", ""]
        lines += [f"- `{p.name}` ({p.location}, {p.type}, {'required' if p.required else 'optional'})" for p in endpoint.parameters] or ["- None specified."]
        lines += ["", "**Responses**", "", f"- Status codes: `{', '.join(endpoint.status_codes or ['200'])}`", ""]
    lines += ["## Schemas", ""]
    for name, fields in api.schemas.items():
        lines.append(f"### `{name}`")
        lines += [f"- `{f.name}`: `{f.type}` ({'required' if f.required else 'optional'})" for f in fields] or ["- Not specified in source."]
    lines += ["", "## Authentication", "", ", ".join(api.security_schemes) if api.security_schemes else "Not specified in source."]
    if quality: lines += ["", f"Documentation Health Score: **{quality.total}/100**"]
    return "\n".join(lines) + "\n"


def generate_html(markdown: str) -> str:
    body = markdown.replace("\n", "<br>\n")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>API Documentation</title></head><body><main>{body}</main></body></html>"


def report_markdown(title: str, items: list[Any]) -> str:
    lines = [f"# {title}", ""]
    for item in items:
        data = item.model_dump() if hasattr(item, "model_dump") else item
        lines.append("- " + "; ".join(f"**{k}**: {v}" for k, v in data.items()))
    return "\n".join(lines) + "\n"


def migration_guide(changes: list[APIChange]) -> str:
    return report_markdown("API Migration Guide", changes) + "\n## Recommended sequence\n\n1. Review HIGH and CRITICAL changes.\n2. Update client models and requests.\n3. Validate against V2 before rollout.\n"


def release_notes(changes: list[APIChange]) -> str:
    groups = {"Added": [], "Changed": [], "Removed": [], "Breaking Changes": []}
    for change in changes:
        if change.kind == "ADDED": groups["Added"].append(change.component)
        elif change.kind == "REMOVED": groups["Removed"].append(change.component)
        else: groups["Changed"].append(change.component)
        if change.severity in {"HIGH", "CRITICAL"}: groups["Breaking Changes"].append(change.component)
    return "\n".join([f"## {name}\n\n" + ("\n".join(f"- {value}" for value in values) or "- None") for name, values in groups.items()]) + "\n"
