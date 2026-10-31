python3 -B - <<'PY'
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
base = root / "artifacts/v1.168-max/cta_max"
p = base / "run_real_sanity_input_adapter.py"

old = 'freq_dir = BASE / "grecbase_integration_weights"'
new = 'freq_dir = BASE / "sequence_weights"'

assert (base / "sequence_weights/fn_rotary_emb_inv_freq.npy").is_file(), "STOP: Rotary weight missing"

s = p.read_text()

if new in s and old not in s:
    print("ROTARY PATH FIX: ALREADY APPLIED")
else:
    assert s.count(old) == 1, "STOP: Unexpected adapter content"
    updated = s.replace(old, new)
    compile(updated, str(p), "exec")
    p.write_text(updated)
    print("ROTARY PATH FIX: APPLIED")

print("ORIGINAL DS CODE: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
