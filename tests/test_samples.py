from pathlib import Path
from parsers.openapi_parser import parse_api
from tools.analysis import compare_versions

ROOT = Path(__file__).parents[1]


def test_sample_versions_demonstrate_evolution():
    v1 = parse_api(file_path=str(ROOT / "sample_apis" / "v1" / "main.py"))
    v2 = parse_api(file_path=str(ROOT / "sample_apis" / "v2" / "main.py"))
    changes = compare_versions(v1, v2)
    assert any(change.kind == "ADDED" and "/orders" in change.component for change in changes)
    assert any(change.kind == "REMOVED" and "DELETE /products" in change.component for change in changes)
