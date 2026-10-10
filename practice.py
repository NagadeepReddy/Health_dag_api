# Fix PyTorch downstream reference
podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "import torch,numpy as np; B='artifacts/v1.168-max/cta_max'; W=B+'/sequence_weights'; x=torch.from_numpy(np.load(B+'/transformer_input.npy')).float(); att=torch.from_numpy(np.load(B+'/transformer_attention_pytorch.npy')).float(); ff=torch.from_numpy(np.load(B+'/transformer_ff_pytorch.npy')).float(); att=att.permute(0,2,1,3).reshape(1,4,512); wa=torch.from_numpy(np.load(W+'/fn_attn_out_weight.npy')).float(); wf=torch.from_numpy(np.load(W+'/fn_ff_out_1_weight.npy')).float(); ng=torch.from_numpy(np.load(W+'/fn_norm2_g.npy')).float(); att_out=torch.nn.functional.linear(att,wa); ff=ff*torch.rsqrt(ff.pow(2).mean(dim=-1,keepdim=True)+1e-6)*ng; xff,gate=ff.chunk(2,dim=-1); ff=torch.nn.functional.silu(gate)*xff; ff_out=torch.nn.functional.linear(ff,wf); final=x+att_out+ff_out; np.save(B+'/transformer_attn_projected_pytorch.npy',att_out.numpy()); np.save(B+'/transformer_ff_out_pytorch.npy',ff_out.numpy()); np.save(B+'/transformer_block0_combined_pytorch.npy',final.numpy()); print('CORRECT SWIGLU PYTORCH REFERENCES SAVED')"

# Fix MAX SwiGLU order
python - <<'PY'
p="artifacts/v1.168-max/cta_max/test_transformer_downstream_max.py"
s=open(p).read()
s=s.replace(
    "swiglu = ops.silu(a) * b",
    "swiglu = a * ops.silu(b)"
)
open(p,"w").write(s)
PY

python -m py_compile artifacts/v1.168-max/cta_max/test_transformer_downstream_max.py && \
podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
artifacts/v1.168-max/cta_max/test_transformer_downstream_max.py
