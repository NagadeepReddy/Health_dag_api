PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, json, shutil, subprocess, textwrap
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = base / "real_max_batch2_backend.py"
backup = base / "real_max_batch2_backend.py.before_ast_batch2_fix"
name = "cta-batch2-trace-8766-10g"

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

print("=== CORRECTED BATCH-2 IMPORT FIX ===", flush=True)

r = subprocess.run(
    pod + ["inspect", name],
    capture_output=True, text=True, timeout=30
)
assert r.returncode == 0, "STOP: Isolated container missing"

info = json.loads(r.stdout)[0]
mounts = info["Mounts"]

def mounted(destination):
    matches = [m for m in mounts if m["Destination"] == destination]
    assert len(matches) == 1, f"STOP: Mount missing: {destination}"
    return matches[0]

candidate_mount = mounted("/batch2")
backend_mount = mounted("/batch2/real_max_batch2_backend.py")

assert Path(backend_mount["Source"]).resolve() == backend.resolve(), \
    "STOP: Backend mount points to different source"

graph = Path(candidate_mount["Source"]) / \
    "cta_max/grecbase_fusion_batch2_draft.py"

assert graph.is_file(), "STOP: Corrected graph unavailable"
assert backend.is_file(), "STOP: Backend unavailable"

graph_text = graph.read_text()
ast.parse(graph_text)
assert "[2, 256]" in graph_text, "STOP: Batch-2 graph declaration absent"

source = backend.read_text()
marker = "# CTA_AST_BATCH2_GRAPH_FIX"

if marker not in source:
    tree = ast.parse(source)

    matches = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom)
        and n.module == "cta_max.grecbase_fusion_full_head_72_max"
        and any(
            alias.name == "build_grecbase_fusion_graph_order_correct"
            for alias in n.names
        )
    ]

    assert len(matches) == 1, \
        "STOP: Original graph import is not uniquely identified"

    node = matches[0]
    lines = source.splitlines(keepends=True)
    original_line = lines[node.lineno - 1]
    indent = original_line[:len(original_line) - len(original_line.lstrip())]

    patch = '''
# CTA_AST_BATCH2_GRAPH_FIX
import importlib.util as _cta_spec_util
import cta_max as _cta_package

_cta_directory = "/batch2/cta_max"
if _cta_directory not in _cta_package.__path__:
    _cta_package.__path__.insert(0, _cta_directory)

_cta_spec = _cta_spec_util.spec_from_file_location(
    "cta_max._verified_isolated_batch2",
    _cta_directory + "/grecbase_fusion_batch2_draft.py"
)
if _cta_spec is None or _cta_spec.loader is None:
    raise RuntimeError("Batch-2 graph loader unavailable")

_cta_module = _cta_spec_util.module_from_spec(_cta_spec)
_cta_spec.loader.exec_module(_cta_module)

build_grecbase_fusion_graph_order_correct = (
    _cta_module.build_grecbase_fusion_graph_order_correct
)
print("CORRECTED BATCH-2 GRAPH: ACTIVE", flush=True)
'''

    insertion = textwrap.indent(
        textwrap.dedent(patch).strip() + "\n", indent
    )

    # AST end_lineno includes every line of a multi-line import.
    lines.insert(node.end_lineno, insertion)
    updated = "".join(lines)

    compile(updated, str(backend), "exec")

    assert not backup.exists(), "STOP: Backup already exists"
    assert shutil.disk_usage(base).free > 20 * 1024 * 1024, \
        "STOP: Low disk space"

    shutil.copy2(backend, backup)
    backend.write_text(updated)
    print("MULTI-LINE IMPORT: FIXED")
    print("BACKUP: PRESERVED")
else:
    print("IMPORT FIX: ALREADY INSTALLED")

compile(backend.read_text(), str(backend), "exec")

print("BATCH-2 GRAPH: VERIFIED")
print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: NOT RESTARTED")
print("ISOLATED CONTAINER: NOT RESTARTED")
print("NEXT: BOUNDED NATIVE HTTP VALIDATION")
PY
