from __future__ import annotations

def plan_tools(request: str) -> list[str]:
    text = request.lower()
    if any(word in text for word in ("compare", "v1", "v2", "breaking", "migration", "release notes")):
        return ["parse_api", "compare_versions", "detect_breaking_changes", "build_impact_graph", "map_changes_to_docs", "generate_migration_guide", "generate_release_notes"]
    if any(word in text for word in ("outdated", "drift", "documentation")):
        return ["parse_api", "parse_documentation", "detect_documentation_drift", "map_changes_to_docs", "calculate_quality_score"]
    if any(word in text for word in ("which", "what changed", "affected", "requires authentication", "explain")):
        return ["retrieve_rag_context", "answer_api_question"]
    return ["parse_api", "extract_schemas", "generate_openapi", "generate_docs", "validate_docs", "calculate_quality_score"]
