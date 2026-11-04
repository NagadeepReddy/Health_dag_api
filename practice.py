cd /application1/sajjna8/rt-pzaas-v1.0 && /opt/venv/bin/python - <<'PY'
from pathlib import Path
from datetime import datetime
import re, shutil

root = Path.cwd()
p = root / "artifacts/v1.472-max/pzaas_max/grecbase_fusion_full_head_72_max.py"

print("=== PZAAS TARGETED SIX-LAYER FIX ===")
assert p.is_file(), f"Graph missing: {p}"
s = p.read_text()
print("ACTIVE GRAPH:", p)
print("CTA REFERENCE: EXCLUDED")

if "seq_raw = postprocess(sx6)" in s:
    print("SIX-LAYER WIRING: ALREADY PRESENT")
else:
    weight_root = root / "artifacts/v1.472-max"
    names = [f.name for f in weight_root.rglob("*.npy")]

    missing = [
        i for i in range(2, 6)
        if not any(
            f"ptransformer.{i}." in n for n in names
        )
    ]
    print("ADDITIONAL LAYER WEIGHTS MISSING:", missing)

    if missing:
        raise SystemExit(
            "STOP: Additional weights must be exported first. No changes."
        )

    patterns = [
        r"(?m)^([ \t]*)block1 = ParallelTransformerBlockMAX\(([^\n]*)\)$",
        r"(?m)^([ \t]*)sx2 = sx1 \+ block1\(sx1, pos, valid_length\)$",
        r"(?m)^([ \t]*)seq_raw = postprocess\(sx2\)$"
    ]
    matches = [list(re.finditer(x, s)) for x in patterns]
    assert all(len(x) == 1 for x in matches), "Graph wiring differs; no changes"
    assert not re.search(r"\bblock[2-5]\s*=", s), "Partial wiring detected"

    decl, step, output = [x[0] for x in matches]
    args = decl.group(2)
    assert len(re.findall(r"layer_idx\s*=\s*1\b", args)) == 1

    blocks = []
    steps = []
    for i in range(2, 6):
        newargs = re.sub(r"layer_idx\s*=\s*1\b", f"layer_idx={i}", args)
        blocks.append(
            f"{decl.group(1)}block{i} = ParallelTransformerBlockMAX({newargs})"
        )
        steps.append(
            f"{step.group(1)}sx{i+1} = sx{i} + block{i}(sx{i}, pos, valid_length)"
        )

    updated = s.replace(
        decl.group(), decl.group() + "\n" + "\n".join(blocks), 1
    ).replace(
        step.group(), step.group() + "\n" + "\n".join(steps), 1
    ).replace(
        output.group(), f"{output.group(1)}seq_raw = postprocess(sx6)", 1
    )

    compile(updated, str(p), "exec")
    backup = p.with_name(p.name + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(p, backup)
    p.write_text(updated)

    print("BACKUP:", backup)
    print("SIX TRANSFORMER LAYERS: SOURCE PASS")

compile(p.read_text(), str(p), "exec")
print("SOURCE SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("REAL MAX COMPILATION: PENDING")
print("FULL MODEL PARITY: PENDING")
print("NATIVE HTTP: PENDING")
PY
