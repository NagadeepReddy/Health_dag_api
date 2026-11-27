export CLOUDSDK_CONFIG="$(mktemp -d /application1/sajjna8/tfy_triton_work/.gcloud-aal.XXXXXX)"


/application1/google-cloud-sdk/bin/gcloud auth activate-service-account \
--key-file=/application1/chellsr/workspace/kubeconfig/service-account-key.json
