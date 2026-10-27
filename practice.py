podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  events --since 1h --until 1s \
  --filter type=container 2>/dev/null \
  | grep -Ei 'cta-max-test|oom|kill|died' | tail -15
