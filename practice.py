cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
grep -nE 'CTAFactoryWrapper|model_factory|start_model_worker|load_scheduler|zmq' artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py
