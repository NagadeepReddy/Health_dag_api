REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import torch, numpy as np, traceback, sys

try:
    from max.driver import CPU, Tensor
    from max.dtype import DType
    from max.graph import Graph, TensorType, DeviceRef
    from max.engine import InferenceSession
    from max.nn import Linear

    state = torch.load(
        "artifacts/v1.113/core-artifact/bplan_model.pt",
        map_location="cpu", weights_only=True
    )
    if "state_dict" in state:
        state = state["state_dict"]

    weight = state["dense1.weight"].detach().cpu().float().numpy()
    assert weight.shape == (10438, 2048)

    device = CPU()
    graph = Graph(
        "bplan_prediction_head",
        input_types=[
            TensorType(DType.float32, [1, 2048],
                       device=DeviceRef.from_device(device))
        ]
    )

    with graph:
        head = Linear(
            in_dim=2048, out_dim=10438,
            dtype=DType.float32,
            device=DeviceRef.from_device(device),
            has_bias=False,
            name="bplan_prediction_head"
        )
        graph.output(head(graph.inputs[0]))

    session = InferenceSession(devices=[device])
    model = session.load(
        graph,
        weights_registry={"bplan_prediction_head.weight": weight}
    )
    print("BPLAN MAX PREDICTION HEAD COMPILE: PASS", flush=True)

    x = np.linspace(-1, 1, 2048, dtype=np.float32).reshape(1, 2048)
    actual = np.asarray(
        model.execute(Tensor.from_numpy(x))[0].to_numpy()
    )
    expected = torch.nn.functional.linear(
        torch.from_numpy(x), torch.from_numpy(weight)
    ).numpy()

    assert actual.shape == expected.shape == (1, 10438)
    diff = float(np.max(np.abs(actual - expected)))
    print("MAX ABS DIFFERENCE:", diff)
    assert np.allclose(actual, expected, rtol=1e-3, atol=1e-4)

    print("BPLAN MAX PREDICTION HEAD PARITY: PASS")
    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN MAX PREDICTION HEAD: FAILED")
    traceback.print_exc()
    sys.exit(1)
PY
