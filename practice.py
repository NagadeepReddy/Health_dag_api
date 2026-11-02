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
        ("[1, 1, 50, 1]", "[1, 1, 20, 1]"),
        ("[1, 1, 50, 256]", "[1, 1, 20, 256]"),
    ],
    adapter: [
        ("page_wide.reshape(1, 50, 1)",
         "page_wide.reshape(1, 20, 1)"),
        ("assert page_in_length == 50",
         "assert page_in_length == 20"),
        ("50-token sequence", "20-token sequence"),
    ],
}

updated = {}

for file, replacements in changes.items():
    assert file.is_file(), f"STOP: missing {file}"
    text = file.read_text()

    for old, new in replacements:
        assert text.count(old) == 1, f"STOP: unexpected pattern {old}"
        text = text.replace(old, new)

    compile(text, str(file), "exec")
    updated[file] = text

for file, text in updated.items():
    backup = file.with_suffix(".py.before_bplan_seq20")
    assert not backup.exists(), f"STOP: backup exists {backup}"

for file, text in updated.items():
    backup = file.with_suffix(".py.before_bplan_seq20")
    backup.write_text(file.read_text())
    file.write_text(text)

print("BPLAN MAX SEQUENCE DIMENSIONS: PASS (20)")
print("JET DIMENSIONS: UNCHANGED (50)")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
