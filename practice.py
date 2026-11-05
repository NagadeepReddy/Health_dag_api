
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none \
--security-opt label=disable \
-v "$PWD:/workspace" \
-w /workspace \
-e PYTHONPATH="/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472-max/pzaas_max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils" \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local - <<'PY'
from pathlib import Path
from types import MethodType
import numpy as np
import torch
import re
import traceback

print("=== PZAAS VERIFIED LIVE 72-INPUT BRIDGE ===", flush=True)

root = Path("/workspace/artifacts/v1.472-max")
native = root / "maxserve_pzaas_extension/pzaas_native_serve_dev"
adapter = native / "pzaas_max_model_adapter.py"
verified = root / "pzaas_max/validation/ppa_packed_inputs_72_verified.npz"

source = r'''
from pathlib import Path
import numpy as np

def pack(model_in, rotary=None):
    def arr(value, dtype):
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()
        return np.ascontiguousarray(np.asarray(value, dtype=dtype))

    def get(name):
        if name not in model_in:
            raise KeyError("Missing original input: " + name)
        return model_in[name]

    task = get("task_in")
    deep = get("deep_in")
    wide = get("wide_in")

    assert len(task) == 2
    assert len(deep) == 17
    assert len(wide) == 127

    result = [
        arr(task[0], np.int64),
        arr(task[1], np.int64),
        arr(get("ihq_in"), np.int64),
        arr(get("jet_name_in"), np.int64),
        arr(get("jet_status_in"), np.int64),
    ]

    result.extend(arr(x, np.int64) for x in deep)

    wide_vector = np.concatenate(
        [arr(x, np.float32).reshape(1, 1) for x in wide],
        axis=1
    )
    result.append(wide_vector)

    result.extend([
        arr(get("input_ids"), np.int64),
        arr(get("attention_mask"), np.int64),
        arr(get("page_in"), np.int64),
        arr(get("item_in"), np.int64),
        arr(get("item_meta_in"), np.int64),
    ])

    page_wide = get("page_meta_wide_in")
    assert len(page_wide) == 1
    result.append(
        arr(page_wide[0], np.float32).reshape(1, 50, 1)
    )

    if rotary is None:
        rotary = np.load(
            Path(__file__).with_name("pzaas_rotary_positions_50.npy"),
            allow_pickle=False
        )
    result.append(arr(rotary, np.float32))

    sibling_deep = arr(get("sibling_deep_in"), np.int64)
    sibling_wide = arr(get("sibling_wide_in"), np.float32)

    assert sibling_deep.shape == (1, 3, 10)
    assert sibling_wide.shape == (1, 18, 10)

    for i in range(10):
        for j in range(3):
            result.append(
                arr(sibling_deep[:, j, i], np.int64)
            )
        result.append(
            arr(sibling_wide[:, :, i], np.float32)
        )

    result.append(arr(get("vl_in"), np.int64))
    result.append(arr(get("sibling_vl_in"), np.int64))

    assert len(result) == 72
    return result
'''

try:
    assert verified.is_file(), f"Missing verified artifact: {verified}"
    assert adapter.is_file(), f"Missing bridge: {adapter}"

    with np.load(verified, allow_pickle=False) as z:
        names = list(z.files)
        indices = [
            re.search(r"(\d+)$", name) for name in names
        ]
        assert len(names) == 72
        assert all(indices), "Saved input ordering not explicit"

        ordered = sorted(
            names,
            key=lambda name: int(re.search(r"(\d+)$", name).group(1))
        )
        assert [
            int(re.search(r"(\d+)$", name).group(1))
            for name in ordered
        ] == list(range(72))

        expected = [z[name].copy() for name in ordered]

    print("VERIFIED GRAPH INPUTS: 72/72", flush=True)

    input_files = list(root.rglob("ppa_model_input_exact.pt"))
    assert len(input_files) == 1, "Exact input source not unique"

    saved = torch.load(
        input_files[0],
        map_location="cpu",
        weights_only=False
    )
    model_in = saved.get("model_in", saved)
    assert isinstance(model_in, dict)

    print("ORIGINAL INPUT: LOADED", flush=True)

    scope = {"__file__": str(native / "pzaas_live_pack_72.py")}
    exec(compile(source, scope["__file__"], "exec"), scope)
    pack = scope["pack"]

    actual = pack(model_in, rotary=expected[29])

    for i, (got, want) in enumerate(zip(actual, expected)):
        assert got.shape == want.shape, (
            f"Input {i}: shape mismatch {got.shape} vs {want.shape}"
        )
        assert got.dtype == want.dtype, (
            f"Input {i}: dtype mismatch {got.dtype} vs {want.dtype}"
        )
        assert np.allclose(got, want, rtol=0, atol=0), (
            f"Input {i}: value mismatch"
        )

    print("LIVE INPUT PACKING: 72/72 PASS", flush=True)

    from pzaas_max_model_adapter import PZAASMAXModel

    model = PZAASMAXModel()
    print("REAL MAX INITIALIZATION: PASS", flush=True)

    model.pack = MethodType(
        lambda self, data: pack(data, rotary=expected[29]),
        model
    )

    result = model(model_in)

    if isinstance(result, (list, tuple)):
        assert len(result) == 1
        result = result[0]

    if hasattr(result, "detach"):
        result = result.detach().cpu().numpy()
    elif hasattr(result, "to_numpy"):
        result = result.to_numpy()

    result = np.asarray(result)
    assert result.shape == (1, 2048), result.shape
    assert np.isfinite(result).all()

    print("REAL MAX FORWARD: PASS", flush=True)
    print("OUTPUT SHAPE:", result.shape, flush=True)

    # Persist only after successful execution.
    helper = native / "pzaas_live_pack_72.py"
    rotary_file = native / "pzaas_rotary_positions_50.npy"

    np.save(rotary_file, expected[29])
    helper.write_text(source)

    marker = "# PZAAS_VERIFIED_LIVE_72_BRIDGE"
    content = adapter.read_text()

    if marker not in content:
        patch = '''
# PZAAS_VERIFIED_LIVE_72_BRIDGE
from pzaas_live_pack_72 import pack as _pzaas_pack72

def _pzaas_verified_pack(self, model_in):
    return _pzaas_pack72(model_in)

PZAASMAXModel.pack = _pzaas_verified_pack
'''
        compile(content + patch, str(adapter), "exec")
        adapter.write_text(content + patch)

    print("NATIVE BRIDGE FIX: SAVED", flush=True)
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("NEXT: NATIVE WORKER AND HTTP 200")

except Exception:
    print("BRIDGE VALIDATION: BLOCKED")
    traceback.print_exc()
    raise SystemExit(1)
PY
