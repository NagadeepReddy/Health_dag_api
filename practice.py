cd /application1/sajjna8/tfy_triton_work

install -d -m 755 aal_triton_stage/input

install -m 644 \
  rt-aal-upg-lead-v1/artifacts/v1.4/samples/load_input_3.json \
  aal_triton_stage/input/load_input_3.json

ls -lh aal_triton_stage/input/
