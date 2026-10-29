cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -C 7 -E \
'pack_two_requests|build_real_inputs|real_sanity|model_in|arrays|execute|allclose|__main__' \
/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/run_batch2_live_max_inference.py
