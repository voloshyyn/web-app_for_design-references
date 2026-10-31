"""
OpenAPI Specification Automated Validator.
Validates structural integrity, schema references, HTTP semantics, and SRS traceability.
Part of SDD Automated Verification Toolchain for Laboratory Work #4.
"""
import sys
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def resolve_ref(doc, ref):
    if not ref.startswith("#/"):
        return None
    parts = ref.lstrip("#/").split("/")
    curr = doc
    for part in parts:
        if part in curr:
            curr = curr[part]
        else:
            return None
    return curr


def validate_openapi(spec_path: Path):
    errors = []
    warnings = []
    stats = {
        "paths_count": 0,
        "operations_count": 0,
        "schemas_count": 0,
        "responses_count": 0,
        "traced_operations": 0
    }

    print(f"[*] Loading OpenAPI specification from: {spec_path}")
    if not spec_path.exists():
        return False, [f"File not found: {spec_path}"], warnings, stats

    content = spec_path.read_text(encoding="utf-8")
    try:
        if spec_path.suffix in [".yaml", ".yml"]:
            if yaml is None:
                return False, ["PyYAML is required to parse YAML specs."], warnings, stats
            spec = yaml.safe_load(content)
        else:
            spec = json.loads(content)
    except Exception as e:
        return False, [f"Syntax parsing error: {e}"], warnings, stats

    # 1. Structural check
    version = spec.get("openapi", "")
    if not version.startswith("3.0"):
        errors.append(f"Invalid or unsupported OpenAPI version: {version}. Expected 3.0.x.")

    info = spec.get("info", {})
    if not info.get("title") or not info.get("version"):
        errors.append("Spec 'info' must contain non-empty 'title' and 'version'.")

    paths = spec.get("paths", {})
    if not paths:
        errors.append("Spec must define at least one path in 'paths'.")

    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    responses = components.get("responses", {})
    stats["schemas_count"] = len(schemas)
    stats["responses_count"] = len(responses)

    # Check for Unified Error Model
    if "ProblemDetails" not in schemas:
        errors.append("Missing required Unified Error Model schema: 'components.schemas.ProblemDetails'.")

    # 2. Paths & Operations check
    http_methods = {"get", "post", "put", "delete", "patch", "options", "head"}

    for path, path_item in paths.items():
        stats["paths_count"] += 1
        path_params_in_url = set(re.findall(r"\{([a-zA-Z0-9_]+)\}", path))
        path_level_params = {p.get("name") for p in path_item.get("parameters", []) if p.get("in") == "path"}

        for method, operation in path_item.items():
            if method.lower() not in http_methods:
                continue
            stats["operations_count"] += 1
            op_id = operation.get("operationId")
            if not op_id:
                errors.append(f"Missing operationId for [{method.upper()} {path}].")

            summary = operation.get("summary")
            if not summary:
                warnings.append(f"Missing summary for [{method.upper()} {path}].")

            tags = operation.get("tags", [])
            if not tags:
                warnings.append(f"Operation [{method.upper()} {path}] has no tags assigned.")

            # Traceability REQ-ID check
            req_ids = operation.get("x-req-id", [])
            if not req_ids:
                warnings.append(f"Operation [{method.upper()} {path}] lacks 'x-req-id' traceability annotation.")
            else:
                stats["traced_operations"] += 1

            # Path parameters matching
            op_params = {p.get("name") for p in operation.get("parameters", []) if p.get("in") == "path"}
            all_path_params = path_level_params.union(op_params)
            missing_params = path_params_in_url - all_path_params
            if missing_params:
                errors.append(f"Path [{method.upper()} {path}] declares URL parameter(s) {missing_params} without matching parameter definition.")

            # Responses check
            op_responses = operation.get("responses", {})
            if not op_responses:
                errors.append(f"Operation [{method.upper()} {path}] defines no responses.")
            
            # Check for error responses
            error_codes = [c for c in op_responses.keys() if c.startswith("4") or c.startswith("5")]
            if not error_codes:
                warnings.append(f"Operation [{method.upper()} {path}] has no 4xx or 5xx error responses defined.")

    # 3. Reference integrity check
    def check_refs(obj, current_path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "$ref" and isinstance(v, str):
                    target = resolve_ref(spec, v)
                    if target is None:
                        errors.append(f"Broken $ref pointer at '{current_path}': unable to resolve '{v}'.")
                else:
                    check_refs(v, f"{current_path}.{k}" if current_path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_refs(item, f"{current_path}[{i}]")

    check_refs(spec)

    is_valid = len(errors) == 0
    return is_valid, errors, warnings, stats


def main():
    workspace = Path(__file__).resolve().parent.parent
    spec_yaml = workspace / "spec" / "openapi.yaml"
    spec_json = workspace / "spec" / "openapi.json"
    log_file = workspace / "logs" / "openapi-validation.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    target_file = spec_yaml if spec_yaml.exists() else spec_json
    is_valid, errors, warnings, stats = validate_openapi(target_file)

    log_lines = [
        "============================================================",
        "OpenAPI Specification Automated Validation Report",
        f"Target Specification: {target_file.name}",
        f"Validation Status: {'PASSED (GO)' if is_valid else 'FAILED (REVISE)'}",
        "============================================================",
        f"Paths Analyzed: {stats['paths_count']}",
        f"Operations Analyzed: {stats['operations_count']}",
        f"Schemas Defined: {stats['schemas_count']}",
        f"Reusable Responses: {stats['responses_count']}",
        f"Operations with x-req-id Traceability: {stats['traced_operations']}/{stats['operations_count']} ({stats['traced_operations']/max(1, stats['operations_count'])*100:.1f}%)",
        "------------------------------------------------------------",
    ]

    if errors:
        log_lines.append(f"ERRORS DETECTED ({len(errors)}):")
        for err in errors:
            log_lines.append(f"  [ERROR] {err}")
    else:
        log_lines.append("ERRORS DETECTED: 0 (Schema and references strictly valid)")

    if warnings:
        log_lines.append(f"WARNINGS ({len(warnings)}):")
        for warn in warnings:
            log_lines.append(f"  [WARN] {warn}")
    else:
        log_lines.append("WARNINGS: 0")

    log_lines.append("============================================================")
    report_text = "\n".join(log_lines)
    print(report_text)
    log_file.write_text(report_text, encoding="utf-8")
    print(f"[*] Full report saved to: {log_file}")

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
