cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
grep -nF -m 5 'model_0_base.pt' artifacts/v1.168-max/run_real_sanity_max_branch_diag.py
