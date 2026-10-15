podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, re, io, contextlib, tempfile
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

BASE = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [
    str(BASE), str(BASE.parent),
    str(Path("artifacts/v1.168/utils/dependency-utils").resolve())
]
from models import ParallelTransformerBlock, RMSNorm

real = torch.load(BASE / "real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)
state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

def w(name):
    return state["sequence_transformer." + name].float()

def make_block(i):
    b = ParallelTransformerBlock(
        dim=256, dim_head=256, heads=2, ff_mult=4).eval()
    prefix = f"sequence_transformer.ptransformer.{i}.fn."
    b.load_state_dict({
        k[len(prefix):]: v for k, v in state.items()
        if k.startswith(prefix)
    }, strict=True)
    return b

b0, b1 = make_block(0), make_block(1)
sn1, sn2 = RMSNorm(256).eval(), RMSNorm(256).eval()
dense = torch.nn.Linear(512, 256).eval()
sn1.load_state_dict({"g": w("out_norm1.g")})
sn2.load_state_dict({"g": w("out_norm2.g")})
dense.load_state_dict({
    "weight": w("seq_dense.weight"),
    "bias": w("seq_dense.bias")
})

with torch.no_grad():
    page = F.embedding(real["page_in"].long(),
                       w("page_embedding.weight"))
    item = F.embedding(real["item_in"].long(),
                       w("item_embedding.weight"))
    meta = F.embedding(real["item_meta_in"].long(),
                       w("item_meta_embedding.weight"))
    pre = F.embedding(real["item_in"].long(),
                      w("item_pre_embedding.weight"))

    wide = real["page_meta_wide_in"]
    if isinstance(wide, (list, tuple)):
        assert len(wide) == 1
        wide = wide[0]
    wide = torch.as_tensor(wide).float()
    assert wide.shape == (1, 50)

    wide = F.leaky_relu(
        F.linear(wide.unsqueeze(-1),
                 w("page_meta_wide_dense.weight"),
                 w("page_meta_wide_dense.bias")),
        negative_slope=0.2)

    x = torch.cat([page, wide], -1) * \
        torch.cat([item, meta, pre], -1)
    assert x.shape == (1, 50, 256)

    x = x + b0(x, real["vl_in"])
    x = x + b1(x, real["vl_in"])
    x = sn1(x)
    pooled = torch.cat([x.mean(1), x.max(1).values], -1)
    pt_sequence = sn2(dense(pooled)).numpy().astype(np.float32)

assert pt_sequence.shape == (1, 256)

original = BASE / "real_sanity_pytorch_same_input_verified.npz"
with np.load(original, allow_pickle=False) as f:
    refs = {k: f[k].copy() for k in f.files}
assert "sequence" in refs
refs["sequence"] = pt_sequence

runner = BASE / "run_real_sanity_max_branch_diag.py"

with tempfile.TemporaryDirectory() as tmp:
    fresh = Path(tmp) / "fresh_refs.npz"
    np.savez(fresh, **refs)

    source = runner.read_text()
    old_name = "real_sanity_pytorch_same_input_verified.npz"
    assert old_name in source
    source = source.replace(old_name, str(fresh))

    # Capture each independent PyTorch comparison reference.
    pattern = (
        r"(?m)^([ \t]*)actual\s*=\s*"
        r"actual\.reshape\(expected\.shape\)[ \t]*$"
    )
    source, count = re.subn(
        pattern,
        lambda m: (
            m.group(1) +
            "pt_branch_refs[name] = "
            "np.asarray(expected, dtype=np.float32).copy()\n" +
            m.group(0)
        ),
        source
    )
    assert count == 1, f"Reference capture locations: {count}"

    scope = {
        "__name__": "__main__",
        "__file__": str(runner),
        "__package__": None,
        "pt_branch_refs": {}
    }

    print("Running existing MAX graph and PyTorch references...",
          flush=True)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        exec(compile(source, str(runner), "exec"), scope)

    for line in log.getvalue().splitlines():
        if "CURRENT BRANCH PARITY:" in line:
            print(line)

    names = [
        "sequence", "context", "search0", "search1",
        "task", "jet", "ihq", "sibling"
    ]
    captured = scope["pt_branch_refs"]
    assert set(names) == set(captured), list(captured)

    pt_branches = torch.from_numpy(np.stack([
        np.asarray(captured[name], dtype=np.float32)
          .reshape(1, 256)
        for name in names
    ], axis=1))

    def substate(prefix):
        return {
            k[len(prefix):]: v
            for k, v in state.items()
            if k.startswith(prefix)
        }

    n1, n2 = RMSNorm(256).eval(), RMSNorm(256).eval()
    att = ParallelTransformerBlock(
        dim=256, dim_head=256, heads=1, ff_mult=4).eval()

    n1.load_state_dict(substate("moe_norm1."), strict=True)
    n2.load_state_dict(substate("moe_norm2."), strict=True)
    att.load_state_dict(substate("att_pooling."), strict=True)

    with torch.no_grad():
        pt_final = n2(att(n1(pt_branches)))
        pt_final = pt_final.reshape(1, 2048).numpy()

    max_final = np.asarray(
        scope["outputs"][0].to_numpy(), dtype=np.float32)

    assert pt_final.shape == max_final.shape == (1, 2048)

    diff = np.abs(
        pt_final.astype(np.float64) -
        max_final.astype(np.float64))

    print("\n=== INDEPENDENT FULL MODEL PARITY ===")
    print("PYTORCH:", pt_final.shape)
    print("MAX:", max_final.shape)
    print("MAX_DIFF:", float(diff.max()))
    print("MEAN_DIFF:", float(diff.mean()))
    print("MATCH:", bool(np.allclose(
        pt_final, max_final, rtol=1e-3, atol=1e-3)))
    print("Original checkpoint/reference files: unchanged")
PY
