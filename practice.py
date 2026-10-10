podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "import torch,numpy as np; B='artifacts/v1.168-max/cta_max'; q=torch.from_numpy(np.load(B+'/transformer_q_rotary_pytorch.npy')).float(); k=torch.from_numpy(np.load(B+'/transformer_k_rotary_pytorch.npy')).float(); v=torch.from_numpy(np.load(B+'/transformer_v_pytorch.npy')).float(); q=q*(256**-0.5); scores=torch.einsum('bhid,bhjd->bhij',q,k); n=scores.shape[-1]; causal=torch.ones((n,n),dtype=torch.bool).triu(1); scores=scores.masked_fill(causal,float('-inf')); attn=torch.softmax(scores,dim=-1); out=torch.einsum('bhij,bhjd->bhid',attn,v); np.save(B+'/transformer_attention_pytorch.npy',out.numpy()); np.save(B+'/transformer_attention_probs_pytorch.npy',attn.numpy()); print('ATTN PROBS:',tuple(attn.shape)); print('ATTN OUTPUT:',tuple(out.shape)); print('PYTORCH ATTENTION REFERENCE SAVED')"
