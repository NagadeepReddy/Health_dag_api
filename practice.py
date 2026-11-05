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

print("=== PZAAS ORIGINAL SEQUENCE STAGE TRACE ===", flush=True)
torch.set_num_threads(2)

root = Path("/workspace/artifacts/v1.472")
validation = Path("/workspace/artifacts/v1.472-max/pzaas_max/validation")

sys.path.insert(0, str(root / "utils/dependency-utils"))
sys.path.insert(0, str(root / "core-artifact"))

try:
    from models import GRecBase

    params_path = root / "config/torch_model_params_base.json"
    params = json.loads(params_path.read_text())
    if isinstance(params, list):
        params = params[0]

    params["nlp_encoder_path"] = str(root / "config/config.json")
    params["transfer_ind"] = True
    params["extract_deep_idx"] = -1

    model = GRecBase(**params)

    state = torch.load(
        root / "core-artifact/model_0_base.pt",
        map_location="cpu",
        weights_only=False
    )
    model.load_state_dict(state, strict=True)
    model.eval()

    print("ORIGINAL MODEL: LOADED")

    saved = torch.load(
        validation / "ppa_model_input_exact.pt",
        map_location="cpu",
        weights_only=False
    )
    model_in = saved["model_in"]

    sig = inspect.signature(model.forward)
    arguments = {
        key: value for key, value in model_in.items()
        if key in sig.parameters
    }

    print("MATCHED FORWARD ARGUMENTS:", len(arguments))

    traces = {}
    handles = []

    def capture(name):
        def hook(module, inputs, output):
            value = output
            if isinstance(value, (tuple, list)):
                value = next(
                    (x for x in value if isinstance(x, torch.Tensor)),
                    None
                )
            if isinstance(value, torch.Tensor):
                traces[name] = value.detach().float().cpu().numpy().copy()
                print(
                    "CAPTURED:", name,
                    "SHAPE:", traces[name].shape,
                    flush=True
                )
        return hook

    for name, module in model.named_modules():
        if name == "sequence_transformer" or name.startswith(
            "sequence_transformer."
        ):
            if (
                name == "sequence_transformer"
                or "embedding" in name
                or "dense" in name
                or "ptransformer" in name
            ):
                handles.append(
                    module.register_forward_hook(capture(name))
                )

    with torch.inference_mode():
        output = model(**arguments)

    for handle in handles:
        handle.remove()

    if isinstance(output, (tuple, list)):
        output = output[0]

    actual = output.detach().cpu().numpy().reshape(1, 2048)

    replay = torch.load(
        validation / "ppa_pytorch_base_replay.pt",
        map_location="cpu",
        weights_only=False
    )
    if isinstance(replay, dict):
        replay = replay["output"]

    expected = (
        replay.detach().cpu().numpy()
        if isinstance(replay, torch.Tensor)
        else np.asarray(replay)
    ).reshape(1, 2048)

    diff = np.abs(actual - expected)

    print("PYTORCH OUTPUT:", actual.shape)
    print("REPLAY MAX DIFF:", float(diff.max()))
    print("REPLAY MEAN DIFF:", float(diff.mean()))

    if not np.allclose(actual, expected, rtol=1e-3, atol=1e-3):
        raise RuntimeError("Original replay consistency failed")

    if not traces:
        raise RuntimeError("No sequence intermediate tensors captured")

    destination = Path("/outputs/ppa_pytorch_sequence_stages.npz")
    np.savez_compressed(
        destination,
        **{
            name.replace(".", "__"): value
            for name, value in traces.items()
        }
    )

    print("\n=== FINAL RESULTS ===")
    print("ORIGINAL PYTORCH: PASS")
    print("SAME-INPUT REPLAY: PASS")
    print("SEQUENCE STAGES CAPTURED:", len(traces))
    print("STAGE TRACE:", destination)
    print("MAX NUMERICAL PARITY: PENDING")
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("NEXT: COMPARE MAX INTERNAL SEQUENCE STAGES")

except Exception as exc:
    print("\nSTAGE CAPTURE: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=4)
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    raise SystemExit(1)
PY
