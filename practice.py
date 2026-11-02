ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
graph = root / "grecbase_fusion_full_head_72_max.py"
adapter = root / "run_real_sanity_input_adapter.py"

changes = {
    graph: [
        ("[1, 50], device=device) for _ in range(3)",
         "[1, 20], device=device) for _ in range(3)"),
        ("[1, 50, 1], device=device)",
         "[1, 20, 1], device=device)"),
        ("[1, 1, 50, 256], device=device)",
         "[1, 1, 20, 256], device=device)"),
    ],
    adapter: [
        ("page_wide.reshape(1, 50, 1)", "page_wide.reshape(1, 20, 1)"),
        ("assert page_in_length == 50", "assert page_in_length == 20"),
    ],
}

updated = {}
for file, replacements in changes.items():
    original = file.read_text()
    new = original
    for old, replacement in replacements:
        count = new.count(old)
        assert count == 1, f"STOP: {file.name}: {old} (found {count})"
        new = new.replace(old, replacement)
    compile(new, str(file), "exec")
    backup = file.with_suffix(".py.before_bplan_seq20")
    assert not backup.exists(), f"STOP: backup exists {backup}"
    updated[file] = (original, new, backup)

for file, (original, new, backup) in updated.items():
    backup.write_text(original)
    file.write_text(new)

print("BPLAN SEQUENCE SHAPES: PASS (20)")
print("JET SHAPES: UNCHANGED (50)")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
