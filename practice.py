cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE 'class CTAMaxPipelineModel|class CTAFactoryWrapper|replace\(llama_arch|pipeline_model=|default_encoding=|supported_encodings|def __call__' \
artifacts/v1.168-max/maxserve_cta_extension/cta_pipeline_model.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py
