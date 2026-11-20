exit
cd /application1/sajjna8/tfy_triton_work

df -h /application1

install -d -m 755 aal_triton_stage/weights

install -m 644 \
  rt-aal-upg-lead-v1/artifacts/v1.4/core-artifact/model_2.pt \
  aal_triton_stage/weights/model_2.pt

ls -lh aal_triton_stage/weights/
