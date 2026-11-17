export TMPDIR=/application1/sajjna8/redis_latency_test/podman_tmp


podman --root /application1/sajjna8/redis_latency_test/podman_graph \
--runroot /application1/sajjna8/redis_latency_test/podman_run \
info --format '{{.Store.GraphRoot}} {{.Store.RunRoot}}'
