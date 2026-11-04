cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import re, hashlib, shutil, datetime

root = Path.cwd()
base = root / "artifacts/v1.472-max/pzaas_max"
matches = list(base.rglob("grecbase_fusion_full_head_72_max.py"))

if len(matches) != 1:
    raise SystemExit("BLOCKED: Exact MAX graph not found uniquely. No changes.")

graph = matches[0]

ds_files = [
    root / "artifacts/v1.472/core-artifact/pipeline.py",
    root / "artifacts/v1.472/utils/dependency-utils/models.py",
]

digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {str(p): digest(p) for p in ds_files if p.is_file()}

source = graph.read_text()
print("=== PZAAS SIX-LAYER MAX ALIGNMENT ===")
print("GRAPH:", graph)

already = (
    all(re.search(
        rf"\bblock{i}\s*=\s*ParallelTransformerBlockMAX\(",
        source
    ) for i in range(6))
    and re.search(
        r"\bseq_raw\s*=\s*postprocess\(\s*sx6\s*\)",
        source
    )
)

if not already:
    if any(re.search(
        rf"\bblock{i}\s*=\s*ParallelTransformerBlockMAX\(",
        source
    ) for i in range(2, 6)):
        raise SystemExit("BLOCKED: Partial layer wiring exists. No changes.")

    patterns = [
        r"(?m)^(?P<pad>[ \t]*)block1[ \t]*=[ \t]*ParallelTransformerBlockMAX\((?P<args>[^\n]*)\)[ \t]*$",
        r"(?m)^(?P<pad>[ \t]*)sx2\s*=\s*sx1\s*\+\s*block1\(\s*sx1\s*,\s*pos\s*,\s*valid_length\s*\)[ \t]*$",
        r"(?m)^(?P<pad>[ \t]*)seq_raw\s*=\s*postprocess\(\s*sx2\s*\)[ \t]*$",
    ]

    found = []
    for pattern in patterns:
        results = list(re.finditer(pattern, source))
        if len(results) != 1:
            raise SystemExit(
                "BLOCKED: Graph layout differs from screenshots. No changes."
            )
        found.append(results[0])

    declaration, step, output = found
    args = declaration.group("args")

    if len(re.findall(r"\blayer_idx\s*=\s*1\b", args)) != 1:
        raise SystemExit("BLOCKED: Layer constructor differs. No changes.")

    declarations = []
    steps = []

    for i in range(2, 6):
        new_args = re.sub(
            r"layer_idx\s*=\s*1\b",
            f"layer_idx={i}",
            args
        )
        declarations.append(
            f"{declaration['pad']}block{i} = "
            f"ParallelTransformerBlockMAX({new_args})"
        )
        steps.append(
            f"{step['pad']}sx{i+1} = sx{i} + "
            f"block{i}(sx{i}, pos, valid_length)"
        )

    updated = source.replace(
        declaration.group(0),
        declaration.group(0) + "\n" + "\n".join(declarations),
        1
    )

    updated = updated.replace(
        step.group(0),
        step.group(0) + "\n" + "\n".join(steps),
        1
    )

    updated = updated.replace(
        output.group(0),
        f"{output['pad']}seq_raw = postprocess(sx6)",
        1
    )

    compile(updated, str(graph), "exec")

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = graph.with_name(graph.name + ".backup_" + stamp)
    shutil.copy2(graph, backup)

    temp = graph.with_name(graph.name + ".temp_six_layers")
    temp.write_text(updated)
    temp.replace(graph)

    print("BACKUP:", backup)
    print("SIX-LAYER GRAPH WIRING: APPLIED")
else:
    print("SIX-LAYER GRAPH WIRING: ALREADY PRESENT")

final = graph.read_text()
compile(final, str(graph), "exec")

for i in range(6):
    assert re.search(
        rf"\bblock{i}\s*=\s*ParallelTransformerBlockMAX\(",
        final
    ), f"Missing layer {i}"

assert re.search(
    r"\bseq_raw\s*=\s*postprocess\(\s*sx6\s*\)",
    final
)

for path, expected in before.items():
    assert digest(Path(path)) == expected

print("SIX-LAYER STRUCTURE: PASS")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNTOUCHED")
print("REAL MAX EXECUTION: PENDING")
print("FULL NUMERICAL PARITY: PENDING")
print("NATIVE HTTP: PENDING")
PY
