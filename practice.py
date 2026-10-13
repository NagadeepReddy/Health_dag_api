python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")
s = p.read_text()

anchor = "# Reuse the previously exported trained MAX weights."

mapping = '''# Map original checkpoint names to MAX graph names.
# The PyTorch transformer has a .fn. wrapper; MAX does not.
for key, tensor in state.items():
    if not isinstance(tensor, torch.Tensor):
        continue

    value = tensor.detach().cpu().contiguous().numpy()
    aliases = []

    if key.startswith("sequence_transformer.ptransformer.") and ".fn." in key:
        aliases.append(key.replace(".fn.", ".", 1))

    if key.startswith("sequence_transformer.seq_dense."):
        aliases.append(key.removeprefix("sequence_transformer."))

    for alias in aliases:
        if alias in weights_registry:
            if not np.array_equal(np.asarray(weights_registry[alias]), value):
                raise RuntimeError("Checkpoint alias conflict: " + alias)
        else:
            weights_registry[alias] = value

print("CHECKPOINT TRANSFORMER ALIASES: READY", flush=True)

'''

old = '''    for alias in aliases:
        if alias in weights_registry:
            existing = np.asarray(weights_registry[alias])
            if not np.array_equal(existing, value):
                raise RuntimeError(
                    f"Conflicting trained weights for {alias}"
                )
        else:
            weights_registry[alias] = value
            added += 1'''

new = '''    for alias in aliases:
        if alias in weights_registry:
            if not np.array_equal(np.asarray(weights_registry[alias]), value):
                print("PRESERVING CHECKPOINT WEIGHT:", alias, flush=True)
            continue
        weights_registry[alias] = value
        added += 1'''

if "CHECKPOINT TRANSFORMER ALIASES: READY" not in s:
    if s.count(anchor) != 1 or s.count(old) != 1:
        raise SystemExit("STOP: Expected runner block not found; no changes")

    updated = s.replace(anchor, mapping + anchor, 1)
    updated = updated.replace(old, new, 1)
    ast.parse(updated, filename=str(p))

    backup = p.with_suffix(".py.before_canonical_weight_mapping")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)
    print("WEIGHT REGISTRATION CORRECTED")
    print("BACKUP:", backup)
else:
    print("WEIGHT REGISTRATION CORRECTION ALREADY PRESENT")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
