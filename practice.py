cd /application1/sajjna8/tfy_triton_work

cp -R rt-aal-upg-lead-v1/artifacts/v1.4/config/. \
  aal_triton_stage/encoder/

chmod -R u+rwX,go+rX aal_triton_stage/encoder/

ls -lh aal_triton_stage/encoder/
