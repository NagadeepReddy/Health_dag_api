TMPDIR=/application1/sajjna8/redis_latency_test/podman_tmp \
podman \
  --root /application1/sajjna8/redis_latency_test/podman_graph \
  --runroot /application1/sajjna8/redis_latency_test/podman_run \
  run --rm --pull=never --network none \
  docker-remote.oneartifactoryci.verizon.com/maven:3.9.11-amazoncorretto-25-al2023 \
  sh -c 'java -version && mvn -version'
