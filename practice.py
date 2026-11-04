cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
from datetime import datetime
import re
import shutil

p = Path("artifacts/v1.472-max/pzaas_max/grecbase_fusion_full_head_72_max.py")

print("=== PZAAS SIX-LAYER GRAPH CORRECTION ===")
assert p.is_file(), f"BLOCKED: Missing {p}"

source = p.read_text()
print("ACTIVE GRAPH:", p)
print("REFERENCE GRAPH: EXCLUDED")

if re.search(r"seq_raw\s*=\s*postprocess\(sx6\)", source):
    print("SIX-LAYER WIRING: ALREADY PRESENT")
else:
    declarations = list(re.finditer(
        r"(?m)^([ \t]*)block1\s*=\s*ParallelTransformerBlockMAX\(([^\n]+)\)$",
        source
    ))
    steps = list(re.finditer(
        r"(?m)^([ \t]*)sx2\s*=\s*sx1\s*\+\s*block1\(sx1,\s*pos,\s*valid_length\)$",
        source
    ))
    outputs = list(re.finditer(
        r"(?m)^([ \t]*)seq_raw\s*=\s*postprocess\(sx2\)$",
        source
    ))

    assert len(declarations) == len(steps) == len(outputs) == 1, (
        "BLOCKED: Existing graph structure differs. No changes."
    )
    assert not re.search(r"(?m)^\s*block[2-5]\s*=", source), (
        "BLOCKED: Partial layer wiring detected. No changes."
    )

    declaration = declarations[0]
    step = steps[0]
    output = outputs[0]

    args = declaration.group(2)
    assert len(re.findall(r"layer_idx\s*=\s*1\b", args)) == 1

    extra_blocks = []
    extra_steps = []

    for i in range(2, 6):
        newargs = re.sub(
            r"layer_idx\s*=\s*1\b",
            f"layer_idx={i}",
            args
        )
        extra_blocks.append(
            f"{declaration.group(1)}block{i} = ParallelTransformerBlockMAX({newargs})"
        )
        extra_steps.append(
            f"{step.group(1)}sx{i+1} = sx{i} + block{i}(sx{i}, pos, valid_length)"
        )

    updated = source.replace(
        declaration.group(),
        declaration.group() + "\n" + "\n".join(extra_blocks),
        1
    ).replace(
        step.group(),
        step.group() + "\n" + "\n".join(extra_steps),
        1
    ).replace(
        output.group(),
        f"{output.group(1)}seq_raw = postprocess(sx6)",
        1
    )

    compile(updated, str(p), "exec")

    backup = p.with_name(
        p.name + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    shutil.copy2(p, backup)
    p.write_text(updated)

    print("BACKUP:", backup)
    print("SIX-LAYER SOURCE WIRING: PASS")

compile(p.read_text(), str(p), "exec")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("SIX-LAYER WEIGHT BINDING: NOT VERIFIED")
print("FULL MAX NUMERICAL PARITY: PENDING")
print("NATIVE HTTP: PENDING")
PY
