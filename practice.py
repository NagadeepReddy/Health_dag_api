python3 - <<'PY'
from pathlib import Path
import ast
import re

root = Path("/application1/BPLAN_MAX_RUNTIME_CLEAN_20261102")
ext = root / "artifacts/v1.113-max/maxserve_bplan_extension"

targets = [
    "bplan_weights.py",
    "live_cta_pipeline_bridge.py",
    "run_batch2_contract.py",
    "bplan_max_projection_parity.py",
    "cta_reference/cta_worker_adapter.py",
]

sources = [
    p for p in root.rglob("*")
    if p.is_file()
    and p.suffix in {".py", ".sh", ".json", ".yaml", ".yml", ".toml"}
    and p.stat().st_size < 2000000
]

for name in targets:
    p = ext / name
    print("\n=== MODULE:", name, "===")

    if not p.is_file():
        print("MISSING")
        continue

    content = p.read_text(errors="replace")

    print("LINES:", len(content.splitlines()))
    print("SIZE:", p.stat().st_size)

    try:
        tree = ast.parse(content)
        definitions = [
            n.name for n in tree.body
            if isinstance(
                n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            )
        ]
        imports = [
            n.module for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom) and n.module
        ]
        imports += [
            alias.name
            for n in ast.walk(tree)
            if isinstance(n, ast.Import)
            for alias in n.names
        ]
        print("DEFINITIONS:", definitions[:15])
        print("IMPORTS:", imports[:20])
    except SyntaxError as e:
        print("SYNTAX ERROR:", e)

    references = []
    for q in sources:
        if q == p:
            continue
        text = q.read_text(errors="replace")
        if re.search(r"\b" + re.escape(p.stem) + r"\b", text):
            references.append(str(q.relative_to(root)))

    print("REFERENCED BY:", len(references))
    for ref in references[:20]:
        print("  ", ref)

    print("FIRST 12 LINES:")
    for line in content.splitlines()[:12]:
        print("  ", line[:150])

print("\n=== DEVELOPMENT ARTIFACT ===")
p = ext / "bplan_max_full_dependency_audit.json"
print("EXISTS:", p.is_file())
print("SIZE:", p.stat().st_size if p.is_file() else 0)

print("\nINSPECTION COMPLETE — NO FILES CHANGED")
PY
