python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")
s = p.read_text()

anchor = "model = session.load(\n    graph, weights_registry=weights_registry\n)"

patch = '''# Reuse the previously exported trained MAX weights.
# Never replace checkpoint values with conflicting exported values.
export_dir = BASE / "grecbase_integration_weights"
if not export_dir.is_dir():
    raise RuntimeError(f"Existing MAX exports not found: {export_dir}")

added = 0
for file in sorted(export_dir.glob("*.npy")):
    name = file.name[:-4]
    value = np.load(file, allow_pickle=False)

    aliases = [name]

    if name.startswith("ptransformer."):
        aliases.append("sequence_transformer." + name)

    if name.startswith("seq_dense."):
        aliases.append("sequence_transformer." + name)

    for alias in aliases:
        if alias in weights_registry:
            existing = np.asarray(weights_registry[alias])
            if not np.array_equal(existing, value):
                raise RuntimeError(
                    f"Conflicting trained weights for {alias}"
                )
        else:
            weights_registry[alias] = value
            added += 1

print("EXISTING MAX EXPORTS REGISTERED:", added)
print("TOTAL REGISTRY ENTRIES:", len(weights_registry))

required_fused = [
    f"sequence_transformer.ptransformer.{i}.fused_attn_ff_proj.weight"
    for i in (0, 1)
]
missing_fused = [
    name for name in required_fused
    if name not in weights_registry
]

if missing_fused:
    print("UNRESOLVED TRANSFORMER WEIGHT NAMES:", missing_fused)
    print("AVAILABLE FUSED WEIGHTS:")
    for name in sorted(weights_registry):
        if "fused_attn_ff_proj" in name:
            print(" ", name, np.asarray(weights_registry[name]).shape)
    raise SystemExit(
        "STOP: Weight-name mapping must be verified before execution"
    )

print("BOTH TRANSFORMER FUSED WEIGHTS REGISTERED: PASS", flush=True)

'''

if "BOTH TRANSFORMER FUSED WEIGHTS REGISTERED: PASS" in s:
    print("EXPORTED WEIGHT REGISTRATION ALREADY ADDED")
elif s.count(anchor) == 1:
    updated = s.replace(anchor, patch + anchor)
    ast.parse(updated, filename=str(p))
    backup = p.with_suffix(".py.before_export_registry_fix")
    if not backup.exists():
        shutil.copy2(p, backup)
    p.write_text(updated)
    print("EXISTING WEIGHT EXPORT REGISTRATION ADDED")
else:
    raise SystemExit("STOP: Unexpected runner structure; nothing changed")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
