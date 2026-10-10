podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "import numpy as np; B='artifacts/v1.168-max/cta_max'; real=np.load(B+'/transformer_pytorch_output.npy'); rebuilt=np.load(B+'/transformer_block0_combined_pytorch.npy'); print('REAL PT SHAPE   :',real.shape); print('REBUILT PT SHAPE:',rebuilt.shape); print('PT REBUILD DIFF :',np.max(np.abs(real-rebuilt))); print('PT REBUILD MATCH:',np.allclose(real,rebuilt,rtol=1e-4,atol=1e-5))"
