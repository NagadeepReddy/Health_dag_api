# Fix PyTorch reference to exact repository RMSNorm
podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "import torch,numpy as np; B='artifacts/v1.168-max/cta_max'; W=B+'/sequence_weights'; x=torch.from_numpy(np.load(B+'/transformer_input.npy')).float(); att=torch.from_numpy(np.load(B+'/transformer_attention_pytorch.npy')).float(); ff=torch.from_numpy(np.load(B+'/transformer_ff_pytorch.npy')).float(); att=att.permute(0,2,1,3).reshape(1,4,512); wa=torch.from_numpy(np.load(W+'/fn_attn_out_weight.npy')).float(); wf=torch.from_numpy(np.load(W+'/fn_ff_out_1_weight.npy')).float(); ng=torch.from_numpy(np.load(W+'/fn_norm2_g.npy')).float(); att_out=torch.nn.functional.linear(att,wa); ff=torch.nn.functional.normalize(ff,dim=-1)*(2048**0.5)*ng; xff,gate=ff.chunk(2,dim=-1); ff=torch.nn.functional.silu(gate)*xff; ff_out=torch.nn.functional.linear(ff,wf); final=x+att_out+ff_out; np.save(B+'/transformer_attn_projected_pytorch.npy',att_out.numpy()); np.save(B+'/transformer_ff_out_pytorch.npy',ff_out.numpy()); np.save(B+'/transformer_block0_combined_pytorch.npy',final.numpy()); print('EXACT RMSNORM + SWIGLU PYTORCH REFERENCES SAVED')"

# Fix MAX norm2 to match F.normalize(x) * sqrt(2048) * g
python - <<'PY'
p="artifacts/v1.168-max/cta_max/test_transformer_downstream_max.py"
s=open(p).read()

old="""rms = ops.rsqrt(ops.mean(fv * fv, axis=-1) + 1.0e-6)
    rms = ops.unsqueeze(rms, -1)
    fn = fv * rms * gamma"""

new="""norm = ops.sqrt(ops.sum(fv * fv, axis=-1))
    norm = ops.unsqueeze(norm, -1)
    fn = (fv / norm) * (2048.0 ** 0.5) * gamma"""

assert old in s, "Expected old norm2 block not found"
s=s.replace(old,new)

open(p,"w").write(s)
PY

python -m py_compile artifacts/v1.168-max/cta_max/test_transformer_downstream_max.py && \
podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
artifacts/v1.168-max/cta_max/test_transformer_downstream_max.py
