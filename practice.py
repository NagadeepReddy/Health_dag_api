
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import ast
import json
import hashlib

shared = Path("/application1/sajjna8/max_shared_infra")

sources = {
    "CTA": Path(
        "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
        "artifacts/v1.168-max/maxserve_cta_extension"
    ),
    "BPLAN": Path(
        "/application1/sajjna8/rt-pzai-bplan-v1/"
        "artifacts/v1.113-max/maxserve_bplan_extension"
    ),
    "PZAAS": Path(
        "/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106/"
        "model/artifacts/v1.472-max/maxserve_pzaas_extension/"
        "pzaas_native_serve_dev"
    )
}

keywords = (
    "scheduler", "router", "queue", "context",
    "worker", "launcher", "registration",
    "factory", "http_pipeline"
)

if not (shared / "bin/run_max_model.sh").is_file():
    raise SystemExit("STOP: Shared launcher missing")

print("=== MULTI-MODEL MAX SERVING INVENTORY ===")
print("SHARED INFRA:", shared)
print("ORIGINAL MODELS: READ-ONLY")

report = {}

for model, root in sources.items():
    print(f"\n=== {model} ===")
    print("SOURCE:", root)

    if not root.is_dir():
        print("SOURCE NOT FOUND - NO PATH GUESSED")
        report[model] = {"status": "source_missing"}
        continue

    components = []

    for path in sorted(root.rglob("*.py")):
        if (
            "__pycache__" in path.parts
            or "_cta_native_reference" in path.parts
            or not any(k in path.name.lower() for k in keywords)
        ):
            continue

        content = path.read_text(errors="replace")

        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            print("SYNTAX REVIEW:", path.name, str(exc))
            continue

        definitions = [
            node.name for node in tree.body
            if isinstance(node, (
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef
            ))
        ]

        imports = sorted({
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
        })

        entry = {
            "path": str(path),
            "lines": len(content.splitlines()),
            "sha256": hashlib.sha256(
                path.read_bytes()
            ).hexdigest(),
            "definitions": definitions,
            "imports": imports
        }

        components.append(entry)

        print(
            f"{path.name}: "
            f"{entry['lines']} lines; "
            f"definitions={','.join(definitions[:5]) or '-'}"
        )

    report[model] = {
        "status": "inspected",
        "component_count": len(components),
        "components": components
    }

    print("SERVING COMPONENTS:", len(components))

destination = shared / "analysis"
destination.mkdir(exist_ok=True)

output = destination / "serve_component_inventory_20261106.json"

if output.exists():
    raise SystemExit(
        "STOP: Inventory already exists. "
        "Existing file preserved."
    )

output.write_text(json.dumps(report, indent=2))

print("\n=== SHARED EXTRACTION READINESS ===")

for model, info in report.items():
    print(
        model,
        "SOURCE:", info["status"],
        "COMPONENTS:", info.get("component_count", 0)
    )

print("INVENTORY:", output)
print("NO MODEL CODE COPIED OR MODIFIED")
print("NO CONTAINERS STARTED OR STOPPED")
print("NEXT: IDENTIFY COMMON IMPLEMENTATIONS")
PY
