podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "import sys,numpy as np,torch; sys.path.insert(0,'artifacts/v1.168/utils/dependency-utils'); from models import ParallelTransformerBlock; B='artifacts/v1.168-max/cta_max'; W=B+'/sequence_weights'; x=torch.from_numpy(np.load(B+'/transformer_input.npy')).float(); m=ParallelTransformerBlock(dim=256,dim_head=256,heads=2,ff_mult=4); sd=m.state_dict(); src={'norm1.g':'fn_norm1_g.npy','norm2.g':'fn_norm2_g.npy','rotary_emb.inv_freq':'fn_rotary_emb_inv_freq.npy','fused_attn_ff_proj.weight':'fn_fused_attn_ff_proj_weight.npy','attn_out.weight':'fn_attn_out_weight.npy','ff_out.1.weight':'fn_ff_out_1_weight.npy'}; [sd[k].copy_(torch.from_numpy(np.load(W+'/'+v))) for k,v in src.items()]; m.load_state_dict(sd); saved={}; h=m.attn_out.register_forward_hook(lambda mod,inp,out: saved.setdefault('attn',out.detach().numpy())); y=m(x); h.remove(); np.save(B+'/transformer_exact_attn_out.npy',saved['attn']); print('ATTN OUT:',saved['attn'].shape); print('FINAL:',tuple(y.shape)); print('EXACT PYTORCH ATTN BOUNDARY SAVED')"
