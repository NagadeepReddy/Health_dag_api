cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run \
--rm -i --pull=never --network=none \
--security-opt label=disable \
-v "$PWD:/workspace:ro" \
-v "$PWD/artifacts/v1.472-max/pzaas_max/validation:/outputs:rw" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, json, inspect, traceback
from pathlib import Path
import numpy as np
import torch

print("=== PZAAS CORRECTED SEQUENCE STAGE CAPTURE ===", flush=True)
torch.set_num_threads(2)

root = Path("/workspace/artifacts/v1.472")
val = Path("/workspace/artifacts/v1.472-max/pzaas_max/validation")

sys.path.insert(0, str(root / "utils/dependency-utils"))
sys.path.insert(0, str(root / "core-artifact"))

try:
    from models import GRecBase

    params = json.loads(
        (root / "config/torch_model_params_base.json").read_text()
    )
    if isinstance(params, list):
        params = params[0]

    params["nlp_encoder_path"] = str(root / "config/config.json")
    params["transfer_ind"] = True
    params["extract_deep_idx"] = -1

    model = GRecBase(**params)

    weights = torch.load(
        root / "core-artifact/model_0_base.pt",
        map_location="cpu",
        weights_only=False
    )

    model.load_state_dict(weights, strict=True)
    model.eval()
    print("ORIGINAL MODEL: PASS", flush=True)

    data = torch.load(
        val / "ppa_model_input_exact.pt",
        map_location="cpu",
        weights_only=False
    )

    if isinstance(data, dict) and "model_in" in data:
        data = data["model_in"]

    if not isinstance(data, dict) or "deep_in" not in data:
        raise RuntimeError(
            "Saved model input structure is unexpected: "
            + str(list(data.keys()) if isinstance(data, dict) else type(data))
        )

    print("SAVED INPUT: PASS", flush=True)

    signature = inspect.signature(model.forward)
    args = {}
    aliases = {"tasks_in": "task_in", "task_in": "tasks_in"}

    for name, param in signature.parameters.items():
        if name == "self":
            continue
        if name in data:
            args[name] = data[name]
        elif aliases.get(name) in data:
            args[name] = data[aliases[name]]
        elif param.default is inspect.Parameter.empty:
            raise RuntimeError("Required input missing: " + name)

    print("FORWARD INPUT MAPPING: PASS", len(args), flush=True)

    stages = {}
    handles = []

    for name, module in model.named_modules():
        if name == "sequence_transformer" or name.startswith(
            "sequence_transformer."
        ):
            def hook(mod, inp, output, stage=name):
                value = output
                if isinstance(value, (list, tuple)):
                    value = next(
                        (x for x in value if isinstance(x, torch.Tensor)),
                        None
                    )
                if isinstance(value, torch.Tensor):
                    stages[stage.replace(".", "__")] = (
                        value.detach().cpu().float().numpy().copy()
                    )

            handles.append(module.register_forward_hook(hook))

    print("SEQUENCE HOOKS:", len(handles), flush=True)

    if not handles:
        raise RuntimeError("Original sequence module not found")

    with torch.inference_mode():
        output = model(**args)

    for handle in handles:
        handle.remove()

    if isinstance(output, (list, tuple)):
        output = output[0]

    actual = output.detach().cpu().numpy().reshape(1, 2048)

    reference = torch.load(
        val / "ppa_model_base_reference.pt",
        map_location="cpu",
        weights_only=False
    )

    if isinstance(reference, torch.Tensor):
        reference = reference.detach().cpu().numpy()

    reference = np.asarray(reference).reshape(1, 2048)
    diff = np.abs(actual - reference)

    print("ORIGINAL OUTPUT:", actual.shape)
    print("REFERENCE MAX DIFF:", float(diff.max()))
    print("REFERENCE MEAN DIFF:", float(diff.mean()))

    if not np.allclose(actual, reference, rtol=1e-3, atol=1e-3):
        raise RuntimeError("Original same-input replay mismatch")

    if not stages:
        raise RuntimeError("No intermediate sequence outputs captured")

    destination = Path("/outputs/ppa_pytorch_sequence_stages.npz")
    np.savez_compressed(destination, **stages)

    print("\n=== FINAL RESULTS ===")
    print("ORIGINAL PYTORCH: PASS")
    print("SAME-INPUT REFERENCE: PASS")
    print("CAPTURED SEQUENCE STAGES:", len(stages))

    for name, value in stages.items():
        print("STAGE:", name, "SHAPE:", value.shape)

    print("TRACE SAVED:", destination)
    print("MAX PARITY: PENDING INTERNAL COMPARISON")
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")

except Exception as exc:
    print("\nSTAGE CAPTURE: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=4)
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    raise SystemExit(1)
PY
