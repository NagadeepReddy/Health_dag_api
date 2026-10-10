podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "import torch,numpy as np; B='artifacts/v1.168-max/cta_max'; x=torch.from_numpy(np.load(B+'/transformer_rms_pytorch.npy')).float(); w=torch.from_numpy(np.load(B+'/sequence_weights/fn_fused_attn_ff_proj_weight.npy')).float(); y=torch.nn.functional.linear(x,w); np.save(B+'/transformer_fused_pytorch.npy',y.numpy()); print('FUSED PT SHAPE:',tuple(y.shape)); print('FUSED PT SAMPLE:',y.flatten()[:5].numpy())"
