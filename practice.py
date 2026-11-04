cd /application1/sajjna8/rt-pzaas-v1.0 || exit 1

python3 - <<'PY'
import ast
import re
from pathlib import Path

root = Path.cwd()
ds = root / "artifacts/v1.472"
mx = root / "artifacts/v1.472-max/pzaas_max"

print("=== PZAAS SEQUENCE PARITY ROOT-CAUSE INSPECTION ===")

def locate_class(folder, classname):
    for p in folder.rglob("*.py"):
        try:
            source = p.read_text(errors="replace")
            if "class " + classname not in source:
                continue
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == classname:
                    return p, source.splitlines(), node
        except (OSError, SyntaxError, UnicodeError):
            continue
    return None

def inspect_class(title, folder, classname, methods, limit):
    print("\n===", title, "===")
    found = locate_class(folder, classname)
    if not found:
        print("CLASS NOT FOUND:", classname)
        return

    path, lines, cls = found
    print("FILE:", path.relative_to(root))

    pattern = re.compile(
        r"embedding|item_pre|page_full|item_full|"
        r"torch\.cat|ops\.concat|transformer|"
        r"ptransformer|block[01]|"
        r"residual|rotary|norm|pool|"
        r"seq_dense|position|return|"
        r"leaky|self\.ff|self\.attn|"
        r"self\.moe|num_layers",
        re.I
    )

    for method in methods:
        funcs = [
            n for n in cls.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == method
        ]
        if not funcs:
            print("METHOD NOT FOUND:", method)
            continue

        node = funcs[0]
        print("METHOD:", method, "LINES:", node.lineno, "-", node.end_lineno)

        selected = [
            (i, lines[i-1].strip())
            for i in range(node.lineno, node.end_lineno + 1)
            if pattern.search(lines[i-1])
            and not lines[i-1].lstrip().startswith("#")
        ]

        for number, line in selected[:limit]:
            print(f"{number}: {line[:160]}")

        if len(selected) > limit:
            print("ADDITIONAL MATCHING LINES:", len(selected) - limit)

inspect_class(
    "ORIGINAL PYTORCH SEQUENCE",
    ds, "ParallelTransformerMAEP",
    ["__init__", "forward"], 35
)

inspect_class(
    "MAX SEQUENCE FEATURES",
    mx, "ParallelTransformerMAEPMAX",
    ["__call__"], 25
)

inspect_class(
    "MAX TRANSFORMER BLOCK",
    mx, "ParallelTransformerBlockMAX",
    ["__call__"], 30
)

inspect_class(
    "MAX POSTPROCESS",
    mx, "SequencePostprocessMAX",
    ["__call__"], 20
)

print("\nPARITY TRIAGE: SOURCE COMPARISON COMPLETE")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: CORRECT FIRST DIVERGENT OPERATION")
PY
