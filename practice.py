python3 -B - <<'PY'
from pathlib import Path
import ast
import shutil

base = Path("/application1")
dev = base / "CTA_MAX_TRUE_BATCH2_DEV_20261029"
candidate = base / "cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
backend = dev / "real_max_batch2_backend.py"

transformer = candidate / "parallel_transformer_block_2layers.py"
nlp = dev / "cta_max/nlp_bert_in_graph.py"

if not all(p.is_file() for p in (backend, transformer, nlp)):
    raise SystemExit("STOP: Required existing source file missing")

src = backend.read_text()

changes = [
    (
        '_b2_dir = "/batch2/cta_max"',
        f'_b2_dir = "{candidate}"'
    ),
    (
        '_b2_pkg.__path__ = [_b2_dir] + [',
        '_b2_pkg.__path__ = [_b2_dir, "/batch2/cta_max"] + ['
    ),
    (
        '_b2_expected = _b2_dir + "/" + _b2_short + ".py"',
        '_b2_expected = (_b2_dir if _b2_short == '
        '"parallel_transformer_block_2layers" '
        'else "/batch2/cta_max") + "/" + _b2_short + ".py"'
    )
]

for old, new in changes:
    if src.count(old) != 1:
        raise SystemExit("STOP: Unexpected backend version: " + old)
    src = src.replace(old, new, 1)

ast.parse(src)

backup = backend.with_name(
    backend.name + ".before_split_helper_fix"
)

if backup.exists():
    raise SystemExit("STOP: Backup already exists")

if shutil.disk_usage(dev).free < 10 * 1024 * 1024:
    raise SystemExit("STOP: Insufficient disk space")

shutil.copy2(backend, backup)
backend.write_text(src)

print("BATCH-2 HELPER PATH FIX: INSTALLED")
print("TRANSFORMER: CORRECTED CANDIDATE")
print("NLP: EXISTING /batch2 SOURCE")
print("SYNTAX: PASS")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
