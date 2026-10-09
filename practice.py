podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import sys, torch
sys.path.insert(0,"artifacts/v1.168/utils/dependency-utils")
from models import ParallelTransformerBlock

m=ParallelTransformerBlock(dim=256, dim_head=256, heads=2, ff_mult=4)
sd=torch.load("artifacts/v1.168/core-artifact/model_0_base.pt",map_location="cpu")

p="sequence_transformer.ptransformer.0.fn."
m.load_state_dict({k[len(p):]:v for k,v in sd.items() if k.startswith(p)},strict=True)

x=torch.randn(1,4,256)
with torch.no_grad():
    xn=m.norm1(x)
    z=m.fused_attn_ff_proj(xn)
    q,k,v,ff=z.split(m.fused_dims,dim=-1)

print("FUSED_DIMS:",m.fused_dims)
print("Q:",tuple(q.shape))
print("K:",tuple(k.shape))
print("V:",tuple(v.shape))
print("FF:",tuple(ff.shape))
print("REAL PYTORCH BLOCK READY")
'
