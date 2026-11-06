ssh -N -L 18770:127.0.0.1:18770 sajjna8@10.119.98.21

http://127.0.0.1:18770/pzaas/predict




scp sajjna8@10.119.98.21:/vzwhome/sajjna8/pzaas_postman_input.json "$env:USERPROFILE\Downloads\pzaas_postman_input.json"



cd /application1/sajjna8/rt-pzaas-v1.0 && \
install -m 600 -o sajjna8 -g "$(id -gn sajjna8)" \
artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json \
/vzwhome/sajjna8/pzaas_postman_input.json && \
cmp -s \
artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json \
/vzwhome/sajjna8/pzaas_postman_input.json && \
ls -l /vzwhome/sajjna8/pzaas_postman_input.json && \
echo "PZAAS POSTMAN FILE: READY FOR WINDOWS DOWNLOAD"
