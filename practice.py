BASE=/application1/sajjna8/redis_latency_test

TMPDIR="$BASE/podman_tmp" podman \
  --root "$BASE/podman_graph" \
  --runroot "$BASE/podman_run" \
  run --rm --pull=never \
  --user "$(id -u sajjna8):$(id -g sajjna8)" \
  --security-opt label=disable \
  -e HOME=/tmp \
  -e MAVEN_OPTS="-Duser.home=/tmp" \
  -v "$BASE/jarvis_build:/workspace:rw" \
  -v "$BASE/maven_cache:/m2:rw" \
  -v "$BASE/maven-settings-public.xml:/settings.xml:ro" \
  -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/maven:3.9.11-amazoncorretto-25-al2023 \
  mvn -B -s /settings.xml \
  -Dmaven.repo.local=/m2 \
  -DskipTests compile
