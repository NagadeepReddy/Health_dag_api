grep -nE '__file__|SOURCE|BASE|WEIGHTS|weights|model_0_base.pt|real_sanity|grecbase_integration_weights|core-artifact' \
  ../cta-max-release-review/cta_max/{serve_max.py,run_live_max_inference.py,run_real_sanity_input_adapter.py,live_cta_pipeline_bridge.py} \
  | head -65
