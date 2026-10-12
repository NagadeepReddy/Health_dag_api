python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
names = [
    "models_raw_attn_diagnostic.py",
    "parallel_transformer_block_layer1_ff.py",
]

prepared = []

for name in names:
    p = base / name
    s = p.read_text()
    lines = s.splitlines()
    tree = ast.parse(s)

    splits = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Tuple)
        and [getattr(x, "id", None) for x in n.targets[0].elts]
            == ["q", "k", "v", "ff"]
    ]

    returns = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Return)
        and isinstance(n.value, ast.Name)
        and n.value.id == "ff"
        and "diagnostic: after norm2" in lines[n.lineno - 1]
    ]

    assert len(splits) == 1, f"STOP {name}: split count={len(splits)}"
    assert len(returns) == 1, f"STOP {name}: return count={len(returns)}"

    split = splits[0]
    ret = returns[0]
    assert split.end_lineno < ret.lineno

    indent = lines[split.lineno - 1][:split.col_offset]
    lines[ret.lineno - 1] = ""
    lines.insert(split.end_lineno, indent + "return ff  # diagnostic: raw ff layer1")

    updated = "\n".join(lines) + "\n"
    ast.parse(updated)

    backup = Path(str(p) + ".before_raw_ff_layer1.bak")
    assert not backup.exists(), f"STOP: backup exists: {backup}"
    prepared.append((p, backup, s, updated))

for p, backup, original, updated in prepared:
    backup.write_text(original)
    p.write_text(updated)
    print("READY:", p.name)

print("BLOCK-1 RAW-FF DIAGNOSTICS READY")
print("REAL MAX BLOCK AND DS CODE UNCHANGED")
PY
