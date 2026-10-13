python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py")
source = p.read_text()

old = '    add("valid_length", get("vl_in", "v1_in"))'

new = '''    # Rotary position tensor for the 50-token sequence.
    # Reuse the exported model frequencies; do not substitute valid_length.
    freq_dir = BASE / "grecbase_integration_weights"
    candidates = sorted(freq_dir.glob("*inv_freq.npy"))
    candidates = [
        f for f in candidates
        if np.load(f).shape == (128,)
    ]
    if not candidates:
        raise RuntimeError("No exported 256-d rotary frequency weights found")

    sequence_candidates = [
        f for f in candidates
        if "seq" in f.name.lower() or "transformer" in f.name.lower()
    ]
    chosen = sequence_candidates or candidates

    inv = np.load(chosen[0]).astype(np.float32)
    for f in chosen[1:]:
        if not np.allclose(inv, np.load(f), rtol=1e-6, atol=1e-7):
            raise RuntimeError("Conflicting rotary frequencies: " + str(f))

    positions = np.arange(page_in_length, dtype=np.float32)[:, None]
    angles = positions * inv[None, :]
    pos = np.concatenate([angles, angles], axis=-1)
    pos = pos.reshape(1, 1, page_in_length, 256)

    print("ROTARY FREQUENCY SOURCE:", chosen[0])
    add("pos", torch.from_numpy(pos.copy()))'''

# The current adapter already supplies page_in with shape (1,50).
new = new.replace(
    'positions = np.arange(page_in_length, dtype=np.float32)[:, None]',
    'page_in_length = int(as_array(get("page_in")).shape[1])\n'
    '    assert page_in_length == 50\n'
    '    positions = np.arange(page_in_length, dtype=np.float32)[:, None]'
)

if old in source:
    updated = source.replace(old, new, 1)
    ast.parse(updated, filename=str(p))

    backup = p.with_suffix(".py.before_rotary_input_fix")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)
    print("ROTARY POSITION INPUT FIXED")
elif 'add("pos", torch.from_numpy(pos.copy()))' in source:
    print("ROTARY POSITION INPUT ALREADY PRESENT")
else:
    raise SystemExit("STOP: Expected adapter code not found; nothing changed")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
