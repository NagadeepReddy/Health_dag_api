podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "import torch,numpy as np; x=torch.from_numpy(np.load('artifacts/v1.168-max/cta_max/transformer_input.npy')).float(); g=torch.from_numpy(np.load('artifacts/v1.168-max/cta_max/sequence_weights/fn_norm1_g.npy')).float(); y=x*torch.rsqrt(x.pow(2).mean(dim=-1,keepdim=True)+1e-6)*g; print('RMS SHAPE:',tuple(y.shape)); print('RMS SAMPLE:',y.flatten()[:10].numpy())"
