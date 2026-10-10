podman run --rm \
-v "$PWD:/workspace" -w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "import numpy as np; B='artifacts/v1.168-max/cta_max'; f=np.load(B+'/transformer_fused_pytorch.npy'); q,k,v,ff=np.split(f,[512,768,1024],axis=-1); q=q.reshape(q.shape[0],q.shape[1],2,256).transpose(0,2,1,3); k=k.reshape(k.shape[0],k.shape[1],1,256).transpose(0,2,1,3); v=v.reshape(v.shape[0],v.shape[1],1,256).transpose(0,2,1,3); np.save(B+'/transformer_q_pytorch.npy',q); np.save(B+'/transformer_k_pytorch.npy',k); np.save(B+'/transformer_v_pytorch.npy',v); print('Q',q.shape,'K',k.shape,'V',v.shape); print('Q/K/V REFERENCES SAVED')"
