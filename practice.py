cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
grep -nE 'model_0_base|torch.load|load_state_dict|CTA\(|pipeline|checkpoint' artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py
