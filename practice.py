PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, re, shutil
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = base / "real_max_batch2_backend.py"
candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)
backup = base / "real_max_batch2_backend.py.before_helper_priority"
marker = "# CTA_BATCH2_EARLY_IMPORT_PRIORITY_V1"

helpers = (
    "nlp_bert_in_graph",
    "parallel_transformer_block_2layers",
)

print("=== BATCH-2 HELPER PRIORITY FIX ===", flush=True)

assert backend.is_file(), "STOP: Backend missing"
assert candidate.is_dir(), "STOP: Candidate missing"

for helper in helpers:
    path = candidate / (helper + ".py")
    assert path.is_file(), f"STOP: Missing {path}"
    ast.parse(path.read_text())

nlp = (candidate / "nlp_bert_in_graph.py").read_text()
assert re.search(r"\[\s*2\s*,\s*1\s*,\s*1\s*,\s*1\s*\]", nlp), \
    "STOP: Candidate batch-2 reshape missing"

source = backend.read_text()
assert "# CTA_AST_BATCH2_GRAPH_FIX" in source, \
    "STOP: Previous graph fix missing"

if marker not in source:
    tree = ast.parse(source)

    anchors = [
        n for n in tree.body
        if (
            isinstance(n, ast.ImportFrom)
            and n.module
            and n.module.startswith("cta_max")
        ) or (
            isinstance(n, ast.Import)
            and any(a.name.startswith("cta_max") for a in n.names)
        )
    ]

    assert anchors, "STOP: No CTA imports found"
    first = min(anchors, key=lambda n: n.lineno)
    assert first.col_offset == 0, "STOP: Unexpected import nesting"

    bootstrap = '''
# CTA_BATCH2_EARLY_IMPORT_PRIORITY_V1
import sys as _cta_b2_sys
import importlib as _cta_b2_importlib
import cta_max as _cta_b2_package

_cta_b2_path = "/batch2/cta_max"
if not __import__("os").path.isfile(
    _cta_b2_path + "/nlp_bert_in_graph.py"
):
    raise RuntimeError("STOP: Batch-2 helper mount missing")

if _cta_b2_path in _cta_b2_package.__path__:
    _cta_b2_package.__path__.remove(_cta_b2_path)
_cta_b2_package.__path__.insert(0, _cta_b2_path)

for _cta_b2_short in (
    "nlp_bert_in_graph",
    "parallel_transformer_block_2layers",
):
    _cta_b2_name = "cta_max." + _cta_b2_short
    _cta_b2_expected = _cta_b2_path + "/" + _cta_b2_short + ".py"
    _cta_b2_cached = _cta_b2_sys.modules.get(_cta_b2_name)

    if _cta_b2_cached is not None and (
        __import__("os").path.realpath(
            getattr(_cta_b2_cached, "__file__", "")
        ) != __import__("os").path.realpath(_cta_b2_expected)
    ):
        del _cta_b2_sys.modules[_cta_b2_name]
        if getattr(_cta_b2_package, _cta_b2_short, None) is _cta_b2_cached:
            delattr(_cta_b2_package, _cta_b2_short)

    _cta_b2_importlib.invalidate_caches()
    _cta_b2_loaded = _cta_b2_importlib.import_module(_cta_b2_name)

    if __import__("os").path.realpath(
        _cta_b2_loaded.__file__
    ) != __import__("os").path.realpath(_cta_b2_expected):
        raise RuntimeError("STOP: Wrong Batch-2 helper: " + _cta_b2_name)

    print("BATCH-2 HELPER ACTIVE:", _cta_b2_loaded.__file__, flush=True)
'''

    lines = source.splitlines(keepends=True)
    lines.insert(first.lineno - 1, bootstrap.strip() + "\n\n")
    updated = "".join(lines)

    compile(updated, str(backend), "exec")

    assert not backup.exists(), "STOP: Backup already exists"
    assert shutil.disk_usage(base).free > 20 * 1024 * 1024, \
        "STOP: Low disk space"

    shutil.copy2(backend, backup)
    backend.write_text(updated)
    print("IMPORT PRIORITY: FIX INSTALLED")
else:
    print("IMPORT PRIORITY: ALREADY INSTALLED")

compile(backend.read_text(), str(backend), "exec")

print("CANDIDATE HELPERS: VERIFIED")
print("SYNTAX: PASS")
print("BACKUP: PRESERVED")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("CONTAINERS: NOT RESTARTED")
print("NEXT: SINGLE NATIVE BATCH-2 VALIDATION")
PY
