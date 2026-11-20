cd /application1/sajjna8/tfy_triton_work

for f in load_input_1.json load_input_2.json sanity_output.json; do
  install -m 644 \
    "rt-aal-upg-lead-v1/artifacts/v1.4/samples/$f" \
    "aal_triton_stage/input/$f"
done

ls -lh aal_triton_stage/input/
