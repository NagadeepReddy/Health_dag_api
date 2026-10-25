cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RInE 'PipelineModel|load_model|load_weights|execute|CTAWorkerAdapter' \
artifacts/v1.168-max/maxserve_cta_extension/*.py | head -60
