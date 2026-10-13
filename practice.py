python - <<'PY'
from pathlib import Path
import ast
import re
import shutil

base = Path("artifacts/v1.168-max/cta_max")
block = base / "parallel_transformer_block_2layers.py"
adapter = base / "run_real_sanity_input_adapter.py"
graphs = [
    base / "grecbase_fusion_order_correct_max.py",
    base / "grecbase_fusion_order_correct_max_branch_diag.py",
]

def replace_once(s, old, new, name):
    if s.count(old) != 1:
        raise RuntimeError(f"{name}: expected exactly one occurrence; found {s.count(old)}")
    return s.replace(old, new, 1)

def patch_block(s):
    if "CTA_DYNAMIC_VALID_LENGTH_MASK" in s:
        return s

    tree = ast.parse(s)
    classes = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef)
        and n.name == "ParallelTransformerBlockMAX"
    ]
    if len(classes) != 1:
        raise RuntimeError("Transformer block class not uniquely found")

    methods = [
        n for n in classes[0].body
        if isinstance(n, ast.FunctionDef) and n.name == "__call__"
    ]
    if len(methods) != 1:
        raise RuntimeError("Transformer __call__ not uniquely found")

    method = methods[0]
    args = [a.arg for a in method.args.args]
    if len(args) != 3 or args[0] != "self":
        raise RuntimeError(f"Unexpected transformer signature: {args}")

    lines = s.splitlines(keepends=True)
    start = sum(map(len, lines[:method.lineno-1]))
    body = sum(map(len, lines[:method.body[0].lineno-1]))
    header = s[start:body]

    close = header.rfind(")")
    if close < 0 or "def __call__" not in header:
        raise RuntimeError("Transformer signature cannot be safely updated")

    prefix = header[:close]
    separator = " " if prefix.rstrip().endswith(",") else ", "
    header_new = (
        prefix + separator + "valid_length=None" + header[close:]
    )
    s = s[:start] + header_new + s[body:]

    pattern = re.compile(
        r"(?m)^([ \t]*)attn\s*=\s*ops\.softmax\(scores\)[ \t]*$"
    )
    matches = list(pattern.finditer(s))
    if len(matches) != 1:
        raise RuntimeError("Expected one attention softmax assignment")

    indent = matches[0].group(1)

    mask_lines = [
        "# CTA_DYNAMIC_VALID_LENGTH_MASK",
        "if valid_length is not None:",
        "    length = int(scores.shape[-1])",
        "    positions = ops.constant(",
        "        np.arange(length, dtype=np.int64).reshape(1, 1, 1, length),",
        "        dtype=DType.int64, device=DeviceRef.CPU()",
        "    )",
        "    valid = ops.reshape(valid_length, [1, 1, 1, 1])",
        "    negative = ops.constant(",
        "        -1.0e9, dtype=scores.dtype, device=DeviceRef.CPU()",
        "    )",
        "    scores = ops.where(positions >= valid, negative, scores)",
        "    causal = np.triu(",
        "        np.ones((length, length), dtype=np.float32), 1",
        "    ) * -1.0e9",
        "    scores = scores + ops.constant(",
        "        causal.reshape(1, 1, length, length),",
        "        dtype=scores.dtype, device=DeviceRef.CPU()",
        "    )",
    ]

    insertion = "\n".join(
        indent + line for line in mask_lines
    )

    s = pattern.sub(
        lambda m: insertion + "\n" + m.group(0),
        s,
        count=1,
    )
    return s

def patch_graph(s):
    if "CTA_DYNAMIC_VALID_LENGTH_INPUT" in s:
        return s

    tree = ast.parse(s)
    functions = [
        n for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and n.name == "build_grecbase_fusion_graph_order_correct"
    ]
    if len(functions) != 1:
        raise RuntimeError("Expected fusion builder not found")

    calls = [
        n for n in ast.walk(functions[0])
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "Graph"
    ]
    if len(calls) != 1:
        raise RuntimeError("Expected one Graph constructor")

    kws = [
        k for k in calls[0].keywords
        if k.arg == "input_types"
    ]
    if len(kws) != 1:
        raise RuntimeError("Graph input_types declaration not found")

    v = kws[0].value
    lines = s.splitlines(keepends=True)
    lo = sum(map(len, lines[:v.lineno-1])) + v.col_offset
    hi = sum(map(len, lines[:v.end_lineno-1])) + v.end_col_offset

    original = s[lo:hi]
    extra = (
        "(" + original + ") + "
        "[TensorType(DType.int64, [1], device=device)]"
    )
    s = s[:lo] + extra + s[hi:]

    pattern = re.compile(
        r"(?m)^([ \t]*sibling_inputs\s*=\s*remaining\[25:65\])[ \t]*$"
    )
    matches = list(pattern.finditer(s))
    if len(matches) != 1:
        raise RuntimeError("Sibling input partition not found")

    indent = re.match(r"[ \t]*", matches[0].group(1)).group()
    s = pattern.sub(
        lambda m: (
            m.group(1)
            + "\n" + indent
            + "valid_length = remaining[65]  # CTA_DYNAMIC_VALID_LENGTH_INPUT"
        ),
        s,
        count=1,
    )

    s = replace_once(
        s, "block0(sx, pos)",
        "block0(sx, pos, valid_length)", "block0 call"
    )
    s = replace_once(
        s, "block1(sx1, pos)",
        "block1(sx1, pos, valid_length)", "block1 call"
    )

    s = re.sub(
        r"assert\s+len\(remaining\)\s*==\s*65",
        "assert len(remaining) == 66",
        s,
    )
    return s

def patch_adapter(s):
    if 'add("valid_length", get("vl_in", "v1_in"))' in s:
        return s

    old = "assert len(inputs) == len(labels) == 70"
    new = (
        'add("valid_length", get("vl_in", "v1_in"))'
        "\n\n    "
        "assert len(inputs) == len(labels) == 71"
    )
    return replace_once(s, old, new, "real-input adapter")

targets = [(block, patch_block), (adapter, patch_adapter)]
targets += [(p, patch_graph) for p in graphs]

prepared = []
for path, transform in targets:
    if not path.is_file():
        raise RuntimeError(f"Missing existing file: {path}")

    before = path.read_text()
    after = transform(before)
    ast.parse(after, filename=str(path))
    prepared.append((path, before, after))

print("ALL FOUR FILES VALIDATED BEFORE WRITING")

for path, before, after in prepared:
    if before == after:
        print("ALREADY UPDATED:", path.name)
        continue

    backup = path.with_suffix(".py.before_valid_length_mask")
    if not backup.exists():
        shutil.copy2(path, backup)

    path.write_text(after)
    print("UPDATED:", path.name)
    print("BACKUP:", backup)

print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py
