from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import yaml

from models.domain import APIModel, EndpointModel, FieldModel, ParameterModel


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def _type_from_schema(schema: dict[str, Any] | None) -> str:
    if not schema:
        return "unknown"
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    return str(schema.get("type", "unknown"))


def _fields(schema: dict[str, Any] | None) -> list[FieldModel]:
    if not schema or schema.get("type") != "object":
        return []
    required = set(schema.get("required", []))
    return [FieldModel(name=name, type=_type_from_schema(value), required=name in required,
                       description=value.get("description", "Not specified in source."))
            for name, value in schema.get("properties", {}).items()]


def parse_openapi(data: dict[str, Any]) -> APIModel:
    info = data.get("info", {})
    components = data.get("components", {})
    schemas = {name: _fields(schema) for name, schema in components.get("schemas", {}).items()}
    security = list(components.get("securitySchemes", {}).keys())
    endpoints: list[EndpointModel] = []
    for path, path_item in data.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            parameters = []
            for parameter in path_item.get("parameters", []) + operation.get("parameters", []):
                schema = parameter.get("schema", {})
                parameters.append(ParameterModel(name=parameter.get("name", "unknown"),
                    location=parameter.get("in", "query"), required=parameter.get("required", False),
                    type=_type_from_schema(schema), description=parameter.get("description", "Not specified in source.")))
            request_fields: list[FieldModel] = []
            body = operation.get("requestBody", {}).get("content", {})
            if body:
                request_fields = _fields(next(iter(body.values())).get("schema", {}))
            response_fields: list[FieldModel] = []
            responses = operation.get("responses", {})
            if responses:
                response = responses.get("200") or responses.get("201") or next(iter(responses.values()))
                content = response.get("content", {}) if isinstance(response, dict) else {}
                if content:
                    response_fields = _fields(next(iter(content.values())).get("schema", {}))
            auth = ["authentication required"] if operation.get("security") else []
            endpoints.append(EndpointModel(method=method.upper(), path=path,
                summary=operation.get("summary", "Not specified in source."),
                description=operation.get("description", "Not specified in source."),
                parameters=parameters, request_fields=request_fields, response_fields=response_fields,
                status_codes=list(responses.keys()), auth=auth, tags=operation.get("tags", []),
                examples=operation.get("examples", {})))
    return APIModel(title=info.get("title", "API"), version=str(info.get("version", "0.0.0")),
                    source_type="openapi", endpoints=endpoints, schemas=schemas,
                    security_schemes=security, auth_required=bool(security))


def parse_openapi_file(path: str | Path) -> APIModel:
    file_path = Path(path)
    content = file_path.read_text(encoding="utf-8")
    data = json.loads(content) if file_path.suffix.lower() == ".json" else yaml.safe_load(content)
    if not isinstance(data, dict) or "openapi" not in data:
        raise ValueError("Expected an OpenAPI 3.x document.")
    return parse_openapi(data)


def _annotation_name(node: ast.AST | None) -> str:
    if node is None:
        return "unknown"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Subscript):
        return ast.unparse(node)
    return ast.unparse(node)


def parse_fastapi_source(source: str) -> APIModel:
    """Static-only parser: parses syntax and decorators, never imports or executes source."""
    tree = ast.parse(source)
    endpoints: list[EndpointModel] = []
    schemas: dict[str, list[FieldModel]] = {}
    auth = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef,)):
            fields = []
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    fields.append(FieldModel(name=child.target.id, type=_annotation_name(child.annotation)))
            if fields:
                schemas[node.name] = fields
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                if decorator.func.attr.lower() not in HTTP_METHODS:
                    continue
                if not decorator.args:
                    continue
                path_node = decorator.args[0]
                path = ast.literal_eval(path_node) if isinstance(path_node, (ast.Constant,)) else "/unknown"
                parameters = [ParameterModel(name=arg.arg, type=_annotation_name(arg.annotation)) for arg in node.args.args]
                endpoints.append(EndpointModel(method=decorator.func.attr.upper(), path=path,
                    summary=ast.get_docstring(node) or "Not specified in source.", parameters=parameters))
            source_text = ast.get_source_segment(source, node) or ""
            if "Depends(get_current_user)" in source_text or "HTTPBearer" in source_text or "OAuth2" in source_text:
                auth.add("Bearer authentication")
    return APIModel(title="FastAPI application", source_type="fastapi_ast", endpoints=endpoints,
                    schemas=schemas, security_schemes=sorted(auth), auth_required=bool(auth))


def parse_api(source: str | None = None, file_path: str | None = None) -> APIModel:
    if file_path:
        path = Path(file_path)
        if path.suffix.lower() in {".yaml", ".yml", ".json"}:
            return parse_openapi_file(path)
        return parse_fastapi_source(path.read_text(encoding="utf-8"))
    if source is None:
        raise ValueError("Provide source or file_path.")
    return parse_openapi(yaml.safe_load(source)) if "openapi:" in source or '"openapi"' in source else parse_fastapi_source(source)
