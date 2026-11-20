cd /application1/sajjna8/tfy_triton_work

install -d -m 755 aal_triton_stage/python

install -m 644 \
  rt-aal-upg-lead-v1/artifacts/v1.4/utils/dependency-utils/models.py \
  aal_triton_stage/python/models.py

ls -l aal_triton_stage/python/
