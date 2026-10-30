
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, re
from pathlib import Path

root = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)
assert root.is_dir(), "STOP: Candidate path missing"

focus = {
    "grecbase_aux_features_max.py",
    "grecbase_fusion_batch2_draft.py",
    "parallel_transformer_block_2layers.py",
    "nlp_bert_in_graph.py",
    "grecbase_get_path_max.py",
}

print("=== ACTIVE BATCH-2 RESHAPE ROOT-CAUSE CHECK ===")

records = []
for path in sorted(root.rglob("*.py")):
    if path.stat().st_size > 500000:
        continue

    src = path.read_text()
    lines = src.splitlines()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in ("reshape", "view"):
            continue

        expr = ast.get_source_segment(src, node) or ""
        expr_flat = " ".join(expr.split())
        if len(expr_flat) > 250:
            expr_flat = expr_flat[:250]

        # Detect fixed, symbolic and inferred shape dimensions.
        target = (
            ast.get_source_segment(src, node.args[-1])
            if node.args else ""
        ) or ""

        target_flat = " ".join(target.split())
        first_one = bool(re.search(
            r"[\[(]\s*1\s*[,)]", target_flat
        ))

        suspicious = (
            first_one
            or "128" in target_flat
            or "-1" in target_flat
            or re.search(r"\bbatch\b|\bbsz\b", target_flat)
        )

        if not suspicious:
            continue

        score = 3
        if re.search(r"[\[(]\s*1\s*,\s*128\s*[\])]", target_flat):
            score = 0
        elif re.search(
            r"[\[(]\s*1\s*,\s*1\s*,\s*1\s*,\s*1\s*[\])]",
            target_flat
        ):
            score = 0
        elif first_one:
            score = 1
        elif "128" in target_flat:
            score = 2

        if path.name in focus:
            score -= 1

        records.append((
            score, str(path), node.lineno,
            expr_flat, lines
        ))

records.sort(key=lambda x: (x[0], x[1], x[2]))

print("CANDIDATE CALLS:", len(records))

for score, name, line, expr, lines in records[:45]:
    print("\nFILE:", name)
    print("LINE:", line)
    print("CALL:", expr)
    for i in range(max(1, line-2), min(len(lines), line+3)+1):
        print(f"{i}: {lines[i-1]}")

print("\n=== POSSIBLE SYMBOLIC SHAPE DEFINITIONS ===")

for filename in sorted(focus):
    path = root / filename
    if not path.is_file():
        continue

    lines = path.read_text().splitlines()
    matches = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if re.search(
            r"\b(batch_size|bsz|batch|seq_len|hidden_size)"
            r"\s*=\s*1\b|"
            r"reshape|"
            r"\bshape\s*=\s*[\[(]\s*1\b",
            line
        )
    ]
    print("\n", filename, "MATCHES:", len(matches))
    for i, line in matches[:25]:
        print(f"{i}: {line[:200]}")

print("\n=== SAFETY ===")
print("FILES MODIFIED: 0")
print("CONTAINERS RESTARTED: 0")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
PY
