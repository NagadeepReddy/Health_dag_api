cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -C 4 \
'PipelineTask|output_type|response_queue|SchedulerZmqConfigs|CTASerializableOutput|pipeline_task' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_http_pipeline.py,cta_native_e2e_test.py,cta_native_scheduler.py} \
| head -110
