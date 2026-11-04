cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import re, shutil, datetime, hashlib

root = Path.cwd()
print("=== PZAAS AUTO-LOCATE + SIX-LAYER ALIGNMENT ===")

matches = []
for p in root.rglob("*.py"):
    if not p.is_file() or p.is_symlink():
        continue
    if not any("max" in part.lower() for part in p.relative_to(root).parts):
        continue
    try:
        s = p.read_text()
    except (OSError, UnicodeError):
        continue
    if re.search(r"(?m)^\s*def build_grecbase_fusion_graph_order_correct\s*\(", s):
        matches.append((p, s))

print("GRAPH CANDIDATES:", len(matches))
for p, _ in matches:
    print("FOUND:", p)

if len(matches) != 1:
    print("=== ADDITIONAL SOURCE LOCATIONS ===")
    for p in root.rglob("*grecbase*max*.py"):
        print("POSSIBLE:", p)
    raise SystemExit("STOP: Unique graph not located. No changes.")

path, source = matches[0]

def one(pattern):
    found = list(re.finditer(pattern, source, re.M))
    if len(found) != 1:
        raise SystemExit(
            "STOP: Expected graph wiring not unique. No changes.\n"
            + pattern
        )
    return found[0]

if all(re.search(
    rf"\bblock{i}\s*=\s*ParallelTransformerBlockMAX\(",
    source
) for i in range(6)) and re.search(
    r"\bseq_raw\s*=\s*postprocess\(sx6\)", source
):
    print("SIX-LAYER GRAPH: ALREADY PRESENT")
else:
    if any(re.search(
        rf"\bblock{i}\s*=\s*ParallelTransformerBlockMAX\(",
        source
    ) for i in range(2, 6)):
        raise SystemExit("STOP: Partial wiring detected. No changes.")

    decl = one(
        r"^([ \t]*)block1\s*=\s*ParallelTransformerBlockMAX\(([^\n]*)\)$"
    )
    step = one(
        r"^([ \t]*)sx2\s*=\s*sx1\s*\+\s*block1\(sx1,\s*pos,\s*valid_length\)$"
    )
    out = one(
        r"^([ \t]*)seq_raw\s*=\s*postprocess\(sx2\)$"
    )

    args = decl.group(2)
    if len(re.findall(r"layer_idx\s*=\s*1\b", args)) != 1:
        raise SystemExit("STOP: Layer constructor mismatch.")

    additions = []
    operations = []

    for i in range(2, 6):
        new_args = re.sub(
            r"layer_idx\s*=\s*1\b",
            f"layer_idx={i}",
            args
        )
        additions.append(
            f"{decl.group(1)}block{i} = "
            f"ParallelTransformerBlockMAX({new_args})"
        )
        operations.append(
            f"{step.group(1)}sx{i+1} = sx{i} + "
            f"block{i}(sx{i}, pos, valid_length)"
        )

    updated = source.replace(
        decl.group(0),
        decl.group(0) + "\n" + "\n".join(additions),
        1
    )
    updated = updated.replace(
        step.group(0),
        step.group(0) + "\n" + "\n".join(operations),
        1
    )
    updated = updated.replace(
        out.group(0),
        f"{out.group(1)}seq_raw = postprocess(sx6)",
        1
    )

    compile(updated, str(path), "exec")

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(path.name + ".backup_" + stamp)
    shutil.copy2(path, backup)

    tmp = path.with_name(path.name + ".six_layer_tmp")
    tmp.write_text(updated)
    tmp.replace(path)

    print("BACKUP:", backup)
    source = updated

compile(source, str(path), "exec")
for i in range(6):
    assert re.search(
        rf"\bblock{i}\s*=\s*ParallelTransformerBlockMAX\(",
        source
    )

assert re.search(r"\bseq_raw\s*=\s*postprocess\(sx6\)", source)

print("GRAPH PATH:", path)
print("SIX TRANSFORMER LAYERS: PASS")
print("MAX SOURCE SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED BY THIS COMMAND")
print("CTA / BPLAN: UNCHANGED")
print("REAL MAX COMPILATION: RECHECK REQUIRED")
print("FULL NUMERICAL PARITY: PENDING")
print("NATIVE HTTP: PENDING")
PY
