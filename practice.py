cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

src = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
dst = Path("artifacts/v1.472-max/pzaas_max")

for _ in range(10):
    missing = set()
    for p in dst.glob("*.py"):
        tree = ast.parse(p.read_text())
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                if n.level == 1 and n.module:
                    missing.add(n.module.split(".")[0])
                elif n.module and n.module.startswith("pzaas_max."):
                    missing.add(n.module.split(".")[1])
                elif n.level == 1 and not n.module:
                    missing.update(x.name for x in n.names)

    needed = sorted(
        name for name in missing
        if not (dst / (name + ".py")).exists()
        and not (dst / name / "__init__.py").exists()
    )
    if not needed:
        break

    for name in needed:
        original = src / (name + ".py")
        if not original.is_file():
            raise SystemExit(f"STOP: Missing source dependency: {name}")
        target = dst / (name + ".py")
        code = original.read_text().replace("cta_max.", "pzaas_max.")
        compile(code, str(target), "exec")
        target.write_text(code)
        print("RESTORED:", name)

for p in dst.glob("*.py"):
    compile(p.read_text(), str(p), "exec")

print("PZAAS LOCAL DEPENDENCIES: RESTORED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
PY
