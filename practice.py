cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/cta_max_true_batch_dev_20261028")
src = base / "cta_max"
entry = src / "grecbase_fusion_full_head_72_max.py"
report = base / "BATCH2_CHANGE_MAP.txt"

assert entry.is_file(), "STOP: Active graph missing"
assert not report.exists(), "STOP: Batch map already exists"

pending = [entry]
visited = set()
lines = ["CTA TRUE BATCH-2 IMPLEMENTATION MAP", ""]

while pending:
    p = pending.pop(0)
    if p in visited:
        continue

    visited.add(p)
    source = p.read_text()
    tree = ast.parse(source)
    blockers = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("cta_max."):
                dependency = src / (
                    node.module.removeprefix("cta_max.").replace(".", "/")
                    + ".py"
                )
                if dependency.is_file() and dependency not in visited:
                    pending.append(dependency)

        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            relevant = (
                "TensorType" in name
                or "reshape" in name
                or "zeros" in name
                or "ones" in name
            )
            if not relevant:
                continue

            fragment = ast.get_source_segment(source, node) or ""
            if "[1," in fragment or "[1]" in fragment or "(1," in fragment:
                blockers.append(
                    f"  line {node.lineno}: "
                    + fragment.splitlines()[0][:150]
                )

    lines.append(f"FILE: {p.relative_to(base)}")
    lines.append(f"SINGLETON-SHAPE CANDIDATES: {len(blockers)}")
    lines.extend(blockers)
    lines.append("")

report.write_text("\n".join(lines) + "\n")

print("ACTIVE GRAPH DEPENDENCY MAP: PASS")
print("ACTIVE PYTHON MODULES:", len(visited))
print("SINGLETON-SHAPE CANDIDATES:",
      sum("SINGLETON-SHAPE CANDIDATES:" in x and
          int(x.split(":")[-1]) or 0
          for x in lines if x.startswith("SINGLETON-SHAPE CANDIDATES:")))

print("\n=== MODULES REQUIRING REVIEW ===")
for line in lines:
    if line.startswith("FILE:") or line.startswith("SINGLETON-SHAPE"):
        print(line)

print("\nREPORT:", report)
print("WORKING HTTP 200: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
