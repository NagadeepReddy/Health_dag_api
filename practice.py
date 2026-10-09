podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c 'import torch, os; s=torch.load("artifacts/v1.168/core-artifact/model_0_base.pt",map_location="cpu"); d="artifacts/v1.168-max/cta_max/sequence_weights"; os.makedirs(d,exist_ok=True); p="sequence_transformer.ptransformer.0."; n=0
for k,v in s.items():
    if k.startswith(p):
        fn=k[len(p):].replace(".","_")+".npy"
        import numpy as np
        np.save(os.path.join(d,fn),v.detach().cpu().numpy())
        print(k,tuple(v.shape))
        n+=1
print("SEQUENCE BLOCK WEIGHTS EXPORTED:",n)'
