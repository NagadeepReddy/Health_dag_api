cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -C 5 \
'class CTA|def predict|def run|async def|model_factory|cta_adapter|start_model_worker' \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py \
| tail -110
