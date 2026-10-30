PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, json, re, shutil, subprocess, textwrap
from pathlib import Path

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-10g"
base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = base / "real_max_batch2_backend.py"

r = subprocess.run(
    pod + ["inspect", name],
    capture_output=True, text=True, timeout=30
)
assert r.returncode == 0, "STOP: Isolated container not found"

info = json.loads(r.stdout)[0]
mounts = [m for m in info["Mounts"]
          if m["Destination"] == "/batch2"]

assert len(mounts) == 1, "STOP: Batch-2 mount ambiguous"
mount = mounts[0]
assert not mount.get("RW", False), "STOP: Candidate mount must be read-only"

candidate = (
    Path(mount["Source"]) /
    "cta_max/grecbase_fusion_batch2_draft.py"
)

print("ACTUAL BATCH-2 GRAPH:", candidate)

assert candidate.is_file(), "STOP: Mounted graph missing"
assert "[2, 256]" in candidate.read_text(), \
    "STOP: Batch-2 input declaration missing"
assert backend.is_file(), "STOP: Isolated backend missing"

source = backend.read_text()

if "_isolated_real_batch2_graph" not in source:
    tree = ast.parse(source)
    imports = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom)
        and n.module == "cta_max.grecbase_fusion_full_head_72_max"
        and any(a.name == "build_grecbase_fusion_graph_order_correct"
                for a in n.names)
    ]

    assert len(imports) == 1, \
        "STOP: Expected one original graph import"

    node = imports[0]
    assert node.lineno == node.end_lineno, \
        "STOP: Multi-line import needs separate handling"

    lines = source.splitlines(keepends=True)
    old = lines[node.lineno - 1]
    indent = old[:len(old) - len(old.lstrip())]

    code = '''
import importlib.util as _cta_util
import cta_max as _cta_pkg

_cta_graph_path = "/batch2/cta_max/grecbase_fusion_batch2_draft.py"
_cta_pkg.__path__ = [
    "/batch2/cta_max",
    *[p for p in _cta_pkg.__path__ if p != "/batch2/cta_max"]
]
_cta_spec = _cta_util.spec_from_file_location(
    "cta_max._isolated_real_batch2_graph",
    _cta_graph_path
)
assert _cta_spec and _cta_spec.loader
_cta_graph = _cta_util.module_from_spec(_cta_spec)
_cta_spec.loader.exec_module(_cta_graph)
build_grecbase_fusion_graph_order_correct = (
    _cta_graph.build_grecbase_fusion_graph_order_correct
)
print("ISOLATED BATCH-2 GRAPH: SELECTED", flush=True)
'''

    lines[node.lineno - 1] = textwrap.indent(
        textwrap.dedent(code).strip() + "\n", indent
    )
    updated = "".join(lines)
    compile(updated, str(backend), "exec")

    backup = backend.with_name(
        "real_max_batch2_backend.py.before_isolated_graph_fix"
    )
    assert not backup.exists(), \
        "STOP: Backup exists; do not overwrite"

    shutil.copy2(backend, backup)
    backend.write_text(updated)
    print("BACKUP: PRESERVED")
else:
    print("GRAPH IMPORT: ALREADY PATCHED")

compile(backend.read_text(), str(backend), "exec")

print("BATCH-2 GRAPH: VERIFIED")
print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("CONTAINERS: NOT RESTARTED")
print("NEXT: ISOLATED NATIVE HTTP VALIDATION")
PY
