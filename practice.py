
cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE -A 12 -B 5 \
'register|architecture|model_factory|resolve|AutoConfig|model_type|PipelineTask' \
artifacts/v1.168-max/maxserve_cta_extension/cta_model_factory.py
