python3 -B - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
pkg = root / "batch2/cta_max"
files = sorted(pkg.glob("*.py"))
missing = set()
dynamic = []
paths = []

for p in files:
    source = p.read_text(errors="replace")
    tree = ast.parse(source, filename=str(p))

    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules = [node.module]
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
            if name in ("import_module", "__import__", "exec", "eval"):
                dynamic.append(f"{p.name}:{node.lineno}:{name}")

        for module in modules:
            if module.startswith("cta_max."):
                rel = module.removeprefix("cta_max.").replace(".", "/")
                if not (pkg / (rel + ".py")).is_file() and not (pkg / rel / "__init__.py").is_file():
                    missing.add(f"{p.name} -> {module}")

    for n, line in enumerate(source.splitlines(), 1):
        if "/application1/" in line or "/workspace/" in line or "/batch2/" in line:
            paths.append(f"{p.name}:{n}: {line.strip()[:130]}")

print("COPIED MODULES:", len(files))
print("MISSING LOCAL IMPORTS:", sorted(missing))
print("DYNAMIC CALLS:", dynamic)
print("HARDCODED PATHS:")
for item in paths:
    print(item)
print("READ-ONLY CHECK COMPLETE")
PY
