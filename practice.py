podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, io, re, tempfile, contextlib
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

B = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [
    str(B), str(B.parent),
    str(Path("artifacts/v1.168/utils/dependency-utils").resolve())
]
from models import ParallelTransformerBlock, RMSNorm

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
state = state.get("state_dict", state)
real = torch.load(B / "real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)

def w(name):
    return state[name].float()

def sub(prefix):
    return {k[len(prefix):]: v for k,v in state.items()
            if k.startswith(prefix)}

def block(i):
    m = ParallelTransformerBlock(
        dim=256, dim_head=256, heads=2, ff_mult=4
    ).eval()
    m.load_state_dict(
        sub(f"sequence_transformer.ptransformer.{i}.fn."),
        strict=True
    )
    return m

nseq1, nseq2 = RMSNorm(256).eval(), RMSNorm(256).eval()
nseq1.load_state_dict({"g": w("sequence_transformer.out_norm1.g")})
nseq2.load_state_dict({"g": w("sequence_transformer.out_norm2.g")})
dense = torch.nn.Linear(512,256).eval()
dense.load_state_dict({
    "weight": w("sequence_transformer.seq_dense.weight"),
    "bias": w("sequence_transformer.seq_dense.bias")
})
b0, b1 = block(0), block(1)

with torch.no_grad():
    p = F.embedding(real["page_in"].long(),
                    w("sequence_transformer.page_embedding.weight"))
    i = F.embedding(real["item_in"].long(),
                    w("sequence_transformer.item_embedding.weight"))
    m = F.embedding(real["item_meta_in"].long(),
                    w("sequence_transformer.item_meta_embedding.weight"))
    pre = F.embedding(real["item_in"].long(),
                    w("sequence_transformer.item_pre_embedding.weight"))

    wide = real["page_meta_wide_in"]
    if isinstance(wide,(tuple,list)):
        assert len(wide)==1
        wide=wide[0]
    wide=torch.as_tensor(wide).float().unsqueeze(-1)
    wide=F.leaky_relu(
        F.linear(wide,
                 w("sequence_transformer.page_meta_wide_dense.weight"),
                 w("sequence_transformer.page_meta_wide_dense.bias")),
        negative_slope=0.2
    )
    x=torch.cat([p,wide],-1)*torch.cat([i,m,pre],-1)
    assert tuple(x.shape)==(1,50,256)
    x=x+b0(x,real["vl_in"])
    x=x+b1(x,real["vl_in"])
    x=nseq1(x)
    x=torch.cat([x.mean(1),x.max(1).values],-1)
    fresh_sequence=nseq2(dense(x)).numpy().astype(np.float32)

assert fresh_sequence.shape==(1,256)

original=B/"real_sanity_pytorch_same_input_verified.npz"
with np.load(original,allow_pickle=False) as f:
    refs={k:f[k].copy() for k in f.files}
refs["sequence"]=fresh_sequence

runner=B/"run_real_sanity_max_branch_diag.py"
source=runner.read_text()
old="real_sanity_pytorch_same_input_verified.npz"
assert old in source

with tempfile.TemporaryDirectory() as temp:
    fresh=Path(temp)/"fresh_refs.npz"
    np.savez(fresh,**refs)
    source=source.replace(old,str(fresh))

    pattern=(r"(?m)^([ \t]*)actual\s*=\s*"
             r"actual\.reshape\(expected\.shape\)[ \t]*$")
    source,count=re.subn(
        pattern,
        lambda m: m.group(1)+
        "pt_refs[name] = np.asarray(expected,dtype=np.float32).copy()\n"+
        m.group(0),source
    )
    assert count==1, f"Reference capture count: {count}"

    scope={
        "__name__":"__main__",
        "__file__":str(runner),
        "__package__":None,
        "pt_refs":{}
    }

    print("Running fresh-reference parity...",flush=True)
    with contextlib.redirect_stdout(io.StringIO()) as log:
        exec(compile(source,str(runner),"exec"),scope)

    for line in log.getvalue().splitlines():
        if "CURRENT BRANCH PARITY:" in line:
            print(line)
            assert "8 /8" in line or "8 / 8" in line, \
                "STOP: Fresh 8/8 parity not confirmed"

    names=["sequence","context","search0","search1",
           "task","jet","ihq","sibling"]
    assert set(scope["pt_refs"])==set(names)

    values=np.stack([
        scope["pt_refs"][name].reshape(1,256)
        for name in names
    ],axis=1)
    inputs=torch.from_numpy(values)

    n1,n2=RMSNorm(256).eval(),RMSNorm(256).eval()
    att=ParallelTransformerBlock(
        dim=256,dim_head=256,heads=1,ff_mult=4
    ).eval()
    n1.load_state_dict(sub("moe_norm1."),strict=True)
    n2.load_state_dict(sub("moe_norm2."),strict=True)
    att.load_state_dict(sub("att_pooling."),strict=True)

    def linear(v,name,bias=False):
        return F.linear(
            v,w(name+".weight"),
            w(name+".bias") if bias else None
        )

    with torch.no_grad():
        z=n2(att(n1(inputs))).reshape(1,2048)
        z=linear(z,"remove_tasks_dense1",True)
        a=linear(z,"remove_tasks_act1.w1")
        b=linear(z,"remove_tasks_act1.w3")
        z=linear(F.silu(a)*b,"remove_tasks_act1.w2")
        pt=z.numpy().astype(np.float32)

    mx=np.asarray(scope["outputs"][0].to_numpy(),
                  dtype=np.float32)
    assert pt.shape==mx.shape==(1,2048)
    difference=np.abs(pt.astype(np.float64)-
                      mx.astype(np.float64))

    print("\n=== FRESH INDEPENDENT FULL-MODEL PARITY ===")
    print("SHAPE:",pt.shape)
    print("MAX_DIFF:",float(difference.max()))
    print("MEAN_DIFF:",float(difference.mean()))
    print("MATCH:",bool(np.allclose(
        pt,mx,rtol=1e-3,atol=1e-3)))
    print("ORIGINAL FILES: UNCHANGED")
PY
