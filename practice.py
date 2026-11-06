ssh -N -L 18770:127.0.0.1:18770 sajjna8@10.119.98.21

http://127.0.0.1:18770/pzaas/predict

Content-Type: application/json

artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json


code -r /application1/sajjna8/rt-pzaas-v1.0/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json



scp root@10.119.98.21:/application1/sajjna8/rt-pzaas-v1.0/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json "$env:USERPROFILE\Downloads\pzaas_postman_input.json"
