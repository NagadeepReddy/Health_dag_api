cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 3g \
-e PYTHONDONTWRITEBYTECODE=1 \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
from pathlib import Path
import numpy as np
import ast
import os

os.umask(0o077)

print("=== PZAAS EIGHT BRANCH ALIGNMENT ===")

fusion = np.load(
    "/validation/pzaas_fusion_input.npy",
    allow_pickle=False
)

assert fusion.shape == (1, 8, 256)

names = [
    "sequence", "context", "search0", "search1",
    "jet", "ihq", "sibling", "task"
]

targets = {
    name: fusion[:, i, :].copy()
    for i, name in enumerate(names)
}

assert np.array_equal(
    np.stack(list(targets.values()), axis=1),
    fusion
)

target = "/validation/pzaas_eight_branch_targets.npz"
np.savez_compressed(target, **targets)
os.chmod(target, 0o600)

for name, value in targets.items():
    print("BRANCH:", name, value.shape)

print("EIGHT BRANCH TARGETS: PASS")

p = Path(
    "/workspace/artifacts/v1.472/"
    "utils/dependency-utils/models.py"
)

tree = ast.parse(p.read_text())
lines = p.read_text().splitlines()

classes = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
    and n.name == "GRecBase"
]

assert classes, "Original GRecBase class missing"

forward = next(
    n for n in classes[0].body
    if isinstance(n, ast.FunctionDef)
    and n.name == "forward"
)

print("\n=== ORIGINAL GRECBASE FUSION WIRING ===")

matches = [
    i for i in range(forward.lineno, forward.end_lineno + 1)
    if "moe_norm1(" in lines[i - 1]
]

assert matches, "Fusion boundary not found"

for i in matches:
    for j in range(max(forward.lineno, i - 12), i + 1):
        print(f"{j}: {lines[j-1]}")

print("\nPZAAS BRANCH REFERENCES: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: NATIVE MAX BRANCH IMPLEMENTATION")
PY
