podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "import sys,torch,numpy as np; sys.path.insert(0,'artifacts/v1.168/utils/dependency-utils'); from models import apply_rotary_pos_emb; B='artifacts/v1.168-max/cta_max'; q=torch.from_numpy(np.load(B+'/transformer_q_pytorch.npy')).float(); k=torch.from_numpy(np.load(B+'/transformer_k_pytorch.npy')).float(); inv=torch.from_numpy(np.load(B+'/sequence_weights/fn_rotary_emb_inv_freq.npy')).float(); seq=torch.arange(q.shape[2],dtype=torch.float32); freqs=torch.einsum('i,j->ij',seq,inv); pos=torch.cat((freqs,freqs),dim=-1)[None,None,:,:]; qr=apply_rotary_pos_emb(pos,q); kr=apply_rotary_pos_emb(pos,k); np.save(B+'/transformer_q_rotary_pytorch.npy',qr.numpy()); np.save(B+'/transformer_k_rotary_pytorch.npy',kr.numpy()); print('Q ROTARY',tuple(qr.shape)); print('K ROTARY',tuple(kr.shape)); print('PYTORCH ROTARY REFERENCES SAVED')"
