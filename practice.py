
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast
import shutil
from pathlib import Path

root = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

assert root.is_dir(), "STOP: Candidate directory missing"

files = {
    "grecbase_aux_features_max.py": "aux",
    "grecbase_fusion_batch2_draft.py": "fusion",
    "nlp_bert_in_graph.py": "nlp",
    "parallel_transformer_block_2layers.py": "length",
    "sequence_transformer_max.py": "length",
}

required = {
    "grecbase_aux_features_max.py",
    "grecbase_fusion_batch2_draft.py",
}

print("=== ACTIVE BATCH-2 FIX ===")

plans = []

for name, mode in files.items():
    path = root / name
    if not path.is_file():
        if name in required:
            raise SystemExit(f"STOP: Missing {path}")
        continue

    original = path.read_text()
    tree = ast.parse(original)
    lines = original.splitlines(keepends=True)
    edits = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "reshape" or len(node.args) < 2:
            continue

        shape = node.args[-1]
        if not isinstance(shape, (ast.List, ast.Tuple)):
            continue
        if not shape.elts:
            continue

        first = shape.elts[0]
        if not isinstance(first, ast.Constant) or first.value != 1:
            continue

        shape_text = ast.unparse(shape)
        value_text = ast.unparse(node.args[0])
        fix = False

        if mode == "aux":
            fix = shape_text in {
                "[1, 2 * dim]",
                "[1, 256]",
                "[1, 1, 128]",
            }

        elif mode == "fusion":
            fix = shape_text in {
                "[1, 1, 128]",
                "[1, 1, 256]",
                "[1, 8, 1]",
                "[1, 2048]",
            }

        elif mode == "nlp":
            fix = (
                "seq_len" in shape_text
                and any(
                    x in value_text
                    for x in (
                        "attention_mask",
                        "ops.gather(",
                        "ops.permute(",
                        "q",
                        "k",
                        "v",
                    )
                )
            )

        elif mode == "length":
            fix = (
                shape_text == "[1, 1, 1, 1]"
                and any(
                    x in value_text
                    for x in (
                        "valid_length",
                        "sequence_length",
                    )
                )
            )

        if not fix:
            continue

        line = first.lineno - 1
        col = first.col_offset

        assert lines[line][col] == "1", (
            f"STOP: Unsafe source position {name}:{line+1}"
        )

        edits.setdefault(line, []).append(col)
        print(f"FIX: {name}:{line+1} {shape_text}")

    for line, positions in edits.items():
        for col in sorted(set(positions), reverse=True):
            lines[line] = (
                lines[line][:col]
                + "2"
                + lines[line][col+1:]
            )

    updated = "".join(lines)
    compile(updated, str(path), "exec")

    if updated != original:
        plans.append((path, original, updated))

if not plans:
    print("STOP: No eligible changes found")
    raise SystemExit(1)

# Verify every patch before modifying any source.
for path, original, updated in plans:
    assert path.is_file()
    assert updated != original
    assert "def " in updated

# Preserve original versions on the same /application1 filesystem.
for path, original, updated in plans:
    backup = path.with_name(
        path.name + ".before_batch2_shape_fix"
    )

    if not backup.exists():
        shutil.copy2(path, backup)
    else:
        assert backup.is_file(), "STOP: Invalid backup"

    temp = path.with_name(path.name + ".batch2_fix_tmp")
    assert not temp.exists(), "STOP: Temporary file already exists"
    temp.write_text(updated)
    compile(temp.read_text(), str(path), "exec")
    temp.replace(path)

print("\n=== RESULTS ===")
print("FILES PATCHED:", len(plans))
print("BATCH SIZE TARGET: 2")
print("SYNTAX: PASS")
print("BACKUPS: PRESERVED")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: NOT RESTARTED")
print("CONTAINERS: NOT RESTARTED")
print("NEXT: BOUNDED NATIVE EXECUTION")
PY
