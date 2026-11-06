
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import ast
import difflib
import hashlib
import json
import re

shared = Path("/application1/sajjna8/max_shared_infra")
analysis = shared / "analysis"

roots = {
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
        "model/artifacts/v1.472-max/maxserve_pzaas_extension"
    )
}

components = [
    "queue_compat",
    "native_scheduler",
    "router",
    "worker_adapter",
    "spawn_worker"
]

output = analysis / "shared_implementation_comparison_20261106.json"

if not (shared / "bin/run_max_model.sh").is_file():
    raise SystemExit("STOP: Shared infrastructure missing")

if output.exists():
    raise SystemExit("STOP: Comparison already exists; not overwritten")

print("=== SHARED MAX IMPLEMENTATION COMPARISON ===")

def normalized(source):
    return re.sub(
        r"cta|bplan|pzaas",
        "model",
        source,
        flags=re.IGNORECASE
    )

def load(model, component):
    root = roots[model]

    if not root.is_dir():
        return {"status": "source_missing"}

    filename = f"{model.lower()}_{component}.py"

    matches = [
        p for p in root.rglob(filename)
        if not any(
            "reference" in part.lower()
            or "backup" in part.lower()
            for part in p.parts
        )
    ]

    if len(matches) != 1:
        return {
            "status": "missing_or_ambiguous",
            "matches": [str(p) for p in matches]
        }

    path = matches[0]
    source = path.read_text(errors="replace")

    try:
        tree = ast.parse(source)
        norm_tree = ast.parse(normalized(source))
    except SyntaxError as exc:
        return {"status": "syntax_error", "error": str(exc)}

    definitions = []
    for node in tree.body:
        if isinstance(node, (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef
        )):
            definitions.append(node.name)

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    return {
        "status": "found",
        "path": str(path),
        "lines": len(source.splitlines()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "definitions": definitions,
        "imports": sorted(set(imports)),
        "normalized_ast": ast.dump(norm_tree),
        "normalized_text": normalized(source)
    }

report = {}

for component in components:
    print(f"\n=== {component.upper()} ===")

    entries = {
        model: load(model, component)
        for model in roots
    }

    report[component] = {}

    for model, item in entries.items():
        report[component][model] = {
            k: v for k, v in item.items()
            if k not in ("normalized_ast", "normalized_text")
        }
        print(
            f"{model}: {item['status']}",
            f"{item.get('lines', 0)} lines",
            f"definitions={','.join(item.get('definitions', [])[:4])}"
        )

    if not all(
        item["status"] == "found"
        for item in entries.values()
    ):
        print("COMPARISON: INCOMPLETE")
        continue

    models = list(entries)
    base = entries[models[0]]

    identical = all(
        entries[m]["normalized_ast"] == base["normalized_ast"]
        for m in models[1:]
    )

    report[component]["normalized_ast_match"] = identical

    print(
        "MODEL-NAME-NORMALIZED AST:",
        "MATCH" if identical else "DIFFERENT"
    )

    for model in models[1:]:
        other = entries[model]

        similarity = difflib.SequenceMatcher(
            None,
            base["normalized_text"],
            other["normalized_text"],
            autojunk=False
        ).ratio()

        print(
            f"CTA vs {model} similarity:",
            f"{similarity:.1%}"
        )

        differences = list(difflib.unified_diff(
            base["normalized_text"].splitlines(),
            other["normalized_text"].splitlines(),
            fromfile="CTA",
            tofile=model,
            lineterm=""
        ))

        report[component][f"CTA_vs_{model}"] = {
            "similarity": round(similarity, 4),
            "diff": differences
        }

    print(
        "EXTRACTION STATUS:",
        "CANDIDATE - REVIEW REQUIRED"
        if identical
        else "REQUIRES ADAPTER DESIGN"
    )

analysis.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2))

print("\n=== RESULT ===")
print("IMPLEMENTATION COMPARISON: COMPLETE")
print("REPORT:", output)
print("ORIGINAL MODEL CODE: UNCHANGED")
print("CTA / BPLAN / PZAAS HANDOFFS: UNCHANGED")
print("RUNNING CONTAINERS: UNCHANGED")
print("NEXT: EXTRACT VERIFIED COMMON COMPONENTS")
PY
