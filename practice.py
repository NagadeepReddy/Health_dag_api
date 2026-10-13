cat > artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py <<'PY'
from pathlib import Path
import torch
import numpy as np

BASE = Path("artifacts/v1.168-max/cta_max")
SOURCE = BASE / "real_sanity_model_in.pt"

data = torch.load(SOURCE, map_location="cpu", weights_only=True)
assert isinstance(data, dict), "Expected saved real-input dictionary"

def get(*names):
    for name in names:
        if name in data:
            return data[name]
    raise KeyError(f"Missing saved input: {names}")

def as_array(x):
    assert isinstance(x, torch.Tensor), type(x)
    return x.detach().cpu().numpy().astype(np.int64)

def combine(items):
    return torch.stack(items, dim=1)

def build_real_inputs():
    inputs = []
    labels = []

    def add(name, tensor):
        inputs.append(as_array(tensor))
        labels.append(name)

    # 5 task / IHQ / JET inputs
    tasks = get("task_in")
    assert len(tasks) == 2
    add("task0", tasks[0])
    add("task1", tasks[1])
    add("ihq_ids", get("ihq_in"))
    add("jet_name", get("jet_name_in"))
    add("jet_status", get("jet_status_in"))

    # 18 context inputs
    deep = get("deep_in")
    wide = get("wide_in")
    assert len(deep) == 17
    assert len(wide) == 127

    for i, tensor in enumerate(deep):
        add(f"context_deep_{i}", tensor)
    add("context_wide", combine(wide))

    # 2 NLP inputs
    add("input_ids", get("input_ids"))
    add("attention_mask", get("attention_mask"))

    # 5 sequence inputs
    add("page", get("page_in"))
    add("item", get("item_in"))
    add("item_meta", get("item_meta_in"))

    page_wide = get("page_meta_wide_in")
    if isinstance(page_wide, (list, tuple)):
        assert len(page_wide) == 1
        page_wide = page_wide[0]
    add("page_wide", page_wide)

    add("valid_length", get("vl_in", "v1_in"))

    # 40 sibling inputs: 3 deep + 1 wide per sibling
    sibling_deep = get("sibling_deep_in")
    sibling_wide = get("sibling_wide_in")

    assert tuple(sibling_deep.shape) == (1, 3, 10)
    assert tuple(sibling_wide.shape) == (1, 18, 10)

    for sibling in range(10):
        for feature in range(3):
            add(
                f"sibling_{sibling}_deep_{feature}",
                sibling_deep[:, feature, sibling]
            )
        add(
            f"sibling_{sibling}_wide",
            sibling_wide[:, :, sibling]
        )

    assert len(inputs) == len(labels) == 70
    assert all(np.issubdtype(x.dtype, np.integer) for x in inputs)

    return labels, inputs

if __name__ == "__main__":
    labels, inputs = build_real_inputs()

    print("=== REAL CTA -> MAX INPUT ADAPTER ===")
    print("REAL INPUT COUNT:", len(inputs))
    print("TASK/IHQ/JET:", len(inputs[:5]))
    print("CONTEXT:", len(inputs[5:23]))
    print("NLP:", len(inputs[23:25]))
    print("SEQUENCE:", len(inputs[25:30]))
    print("SIBLING:", len(inputs[30:70]))

    for i, (name, value) in enumerate(zip(labels, inputs)):
        if i < 30 or i in (30, 33, 66, 69):
            print(i, name, value.shape)

    print("REAL CTA INPUT MAPPING: PASS")
    print("ORIGINAL PYTORCH/DS FILES UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py
