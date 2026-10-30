PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast
import re
import shutil
import textwrap
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = base / "real_max_batch2_backend.py"
graph = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/grecbase_fusion_batch2_draft.py"
)
backup = backend.with_name(
    "real_max_batch2_backend.py.before_graph_override_v2"
)

print("=== ISOLATED GRAPH IMPORT FIX ===")

assert backend.is_file(), "STOP: Backend missing"
assert graph.is_file(), "STOP: Corrected graph missing"

graph_source = graph.read_text()
ast.parse(graph_source)

assert re.search(r"\[\s*2\s*,\s*256\s*\]", graph_source), \
    "STOP: Batch-2 graph declaration missing"

source = backend.read_text()
marker = "CTA_ISOLATED_BATCH2_GRAPH_OVERRIDE_V2"

if marker in source:
    print("GRAPH OVERRIDE: ALREADY INSTALLED")
else:
    tree = ast.parse(source)

    matches = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom)
        and n.module
        and "grecbase" in n.module
        and any(
            a.name == "build_grecbase_fusion_graph_order_correct"
            for a in n.names
        )
    ]

    assert len(matches) == 1, \
        "STOP: Expected exactly one original graph import"

    node = matches[0]

    # Insert AFTER the full import, including multi-line imports.
    indent = " " * node.col_offset

    override = '''
# CTA_ISOLATED_BATCH2_GRAPH_OVERRIDE_V2
import importlib.util as _cta_graph_util
import cta_max as _cta_graph_pkg

_cta_graph_dir = "/batch2/cta_max"
_cta_graph_pkg.__path__ = list(
    dict.fromkeys(
        list(_cta_graph_pkg.__path__) + [_cta_graph_dir]
    )
)

_cta_graph_file = (
    "/batch2/cta_max/grecbase_fusion_batch2_draft.py"
)

_cta_graph_spec = _cta_graph_util.spec_from_file_location(
    "cta_max._isolated_batch2_graph_v2",
    _cta_graph_file
)

if _cta_graph_spec is None or _cta_graph_spec.loader is None:
    raise RuntimeError("STOP: Batch-2 graph loader unavailable")

_cta_graph_module = _cta_graph_util.module_from_spec(
    _cta_graph_spec
)
_cta_graph_spec.loader.exec_module(_cta_graph_module)

build_grecbase_fusion_graph_order_correct = (
    _cta_graph_module.build_grecbase_fusion_graph_order_correct
)

print("ISOLATED BATCH-2 GRAPH OVERRIDE: ACTIVE", flush=True)
'''

    lines = source.splitlines(keepends=True)
    addition = textwrap.indent(
        textwrap.dedent(override).strip() + "\n",
        indent
    )

    lines.insert(node.end_lineno, addition)
    updated = "".join(lines)

    compile(updated, str(backend), "exec")

    assert not backup.exists(), \
        "STOP: Backup already exists; no overwrite"

    assert shutil.disk_usage(base).free > 20 * 1024 * 1024, \
        "STOP: Insufficient disk space"

    shutil.copy2(backend, backup)
    backend.write_text(updated)

    print("MULTI-LINE IMPORT: FIXED")
    print("BACKUP: PRESERVED")

compile(backend.read_text(), str(backend), "exec")

print("SYNTAX: PASS")
print("BATCH-2 GRAPH: SELECTED")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("CONTAINERS: NOT RESTARTED")
print("NEXT: ISOLATED NATIVE HTTP VALIDATION")
PY
