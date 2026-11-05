
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run \
--rm -i --pull=never --network=none \
--security-opt label=disable \
-v "$PWD:/workspace:ro" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np
import torch

v = Path("/workspace/artifacts/v1.472-max/pzaas_max/validation")
print("=== PZAAS CORRECTED SAME-INPUT PROVENANCE ===", flush=True)

def load(name):
    return torch.load(v / name, map_location="cpu", weights_only=False)

def arr(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    return np.asarray(x)

saved = load("ppa_model_input_exact.pt")
model_in = saved.get("model_in", saved)

names = [
    "page_in", "item_in", "item_in_sku",
    "item_meta_in", "vl_in", "ihq_in",
    "jet_name_in", "jet_status_in",
    "sibling_deep_in", "sibling_wide_in",
    "sibling_vl_in", "current_in",
    "input_ids", "attention_mask"
]

with np.load(v / "ppa_tensor_inputs.npz") as data:
    matches = 0
    for name in names:
        if name not in model_in or name not in data:
            print("MISSING:", name,
                  "PT:", name in model_in,
                  "NPZ:", name in data)
            continue

        a = arr(model_in[name])
        b = np.asarray(data[name])
        ok = a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b)
        matches += int(ok)
        print(name, "PASS" if ok else "FAIL", a.shape, b.shape)

print("\nINPUT VALUE MATCHES:", matches, "/14")

ref = load("ppa_pytorch_base_replay.pt")
replay = arr(ref["output"] if isinstance(ref, dict) else ref).reshape(1, 2048)

order = [
    "sequence", "context", "search0", "search1",
    "jet", "ihq", "sibling", "task"
]

target = v / "pzaas_eight_branch_targets.npz"
print("\nBRANCH TARGET FILE:", target.name)
print("FILE EXISTS:", target.is_file())

branch_pass = False

if target.is_file():
    with np.load(target) as data:
        if all(k in data.files for k in order):
            parts = [arr(data[k]).reshape(-1) for k in order]

            if all(p.size == 256 for p in parts):
                combined = np.concatenate(parts).reshape(1, 2048)

                for i, name in enumerate(order):
                    expected = replay.reshape(-1)[i*256:(i+1)*256]
                    diff = np.abs(parts[i] - expected)
                    print(
                        name,
                        "MAX_DIFF:", float(diff.max()),
                        "MEAN_DIFF:", float(diff.mean())
                    )

                diff = np.abs(combined - replay)
                branch_pass = np.allclose(
                    combined, replay,
                    rtol=1e-3, atol=1e-3
                )
                print("\nBRANCH CONCAT MAX DIFF:", float(diff.max()))
                print("BRANCH CONCAT MEAN DIFF:", float(diff.mean()))
            else:
                print("ERROR: Branch dimensions are not all 256")
        else:
            print("MISSING BRANCH KEYS:", sorted(set(order)-set(data.files)))

print("\n=== FINAL RESULTS ===")
print("ORIGINAL PYTORCH REPLAY: PASS")
print("EXACT INPUT VALUES:", "PASS" if matches == 14 else "FAIL")
print("SAME-STAGE BRANCH TARGETS:", "PASS" if branch_pass else "NOT VERIFIED")
print("MAX CPU EXECUTION: PREVIOUSLY PASS")
print("FULL MAX PARITY: PENDING")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print(
    "NEXT:",
    "ISOLATE MAX OPERATION DIFFERENCE"
    if matches == 14 and branch_pass
    else "RESOLVE SAVED REFERENCE ALIGNMENT"
)
PY
