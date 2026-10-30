PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import json
import subprocess
from pathlib import Path

pod = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
]
name = "cta-batch2-trace-8766-10g"

info = json.loads(subprocess.check_output(
    pod + ["inspect", name], text=True
))[0]

assert info["State"]["Status"] == "running", \
    "STOP: Isolated container is not running"

mount = next(
    (m for m in info["Mounts"]
     if m["Destination"] == "/batch2"),
    None
)
assert mount, "STOP: /batch2 mount missing"

root = Path(mount["Source"]).resolve()
assert str(root).startswith("/application1/"), \
    "STOP: Unexpected mount source"

pkg = root / "cta_max"
assert pkg.is_dir(), "STOP: Candidate package missing"

required = [
    "grecbase_fusion_batch2_draft.py",
    "grecbase_aux_features_max.py",
    "grecbase_aux_branches_max.py",
    "parallel_transformer_block_2layers.py",
    "nlp_bert_in_graph.py",
]
assert all((pkg / n).is_file() for n in required), \
    "STOP: Candidate helper missing"

hook = root / "sitecustomize.py"
marker = "# CTA_BATCH2_IMPORT_PRIORITY"

patch = '''
# CTA_BATCH2_IMPORT_PRIORITY
from pathlib import Path as _CTAP
import cta_max as _cta_pkg
_cta_overlay = "/batch2/cta_max"
if _CTAP(_cta_overlay).is_dir():
    if _cta_overlay in _cta_pkg.__path__:
        _cta_pkg.__path__.remove(_cta_overlay)
    _cta_pkg.__path__.insert(0, _cta_overlay)
'''

old = hook.read_text() if hook.exists() else None

if old is not None and marker in old:
    print("IMPORT FIX: ALREADY PRESENT")
else:
    if old is not None:
        backup = root / "sitecustomize.py.before_batch2_import"
        assert not backup.exists(), "STOP: Backup exists"
        backup.write_text(old)
        print("BACKUP: PRESERVED")

    new = (old or "") + "\n" + patch
    compile(new, str(hook), "exec")
    hook.write_text(new)
    print("IMPORT FIX: INSTALLED")

test = r'''
import importlib.util
import cta_max
from pathlib import Path

print("PACKAGE:", cta_max.__file__)
print("SEARCH FIRST:", cta_max.__path__[0])

assert cta_max.__path__[0] == "/batch2/cta_max"

names = [
    "grecbase_aux_features_max",
    "grecbase_aux_branches_max",
    "parallel_transformer_block_2layers",
    "nlp_bert_in_graph",
]

for name in names:
    spec = importlib.util.find_spec("cta_max." + name)
    assert spec and spec.origin, name
    print(name, "=>", spec.origin)
    assert Path(spec.origin).resolve().is_relative_to(
        Path("/batch2/cta_max").resolve()
    ), "WRONG IMPORT: " + name

print("BATCH-2 IMPORT PRIORITY: PASS")
'''

try:
    subprocess.run(
        pod + [
            "exec", "-i",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            name, "/opt/venv/bin/python", "-B", "-c", test
        ],
        check=True,
        timeout=40
    )
except Exception:
    if old is None:
        hook.unlink(missing_ok=True)
    else:
        hook.write_text(old)
    print("STOP: Validation failed; original hook restored")
    raise

print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("NEXT: BOUNDED ISOLATED NATIVE HTTP RETEST")
PY
