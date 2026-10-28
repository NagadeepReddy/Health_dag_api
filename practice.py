for name in eloquent_ishizaka strange_pascal priceless_volhard musing_wu; do
  echo "Checking: $name"

  if podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    inspect "$name" \
    --format '{{json .Config.Cmd}}' 2>/dev/null \
    | grep -Fq 'cta_native_e2e_test.py'; then

    podman \
      --root /application1/podman/storage \
      --runroot /run/containers/storage \
      stop --time 10 "$name"
  else
    echo "SKIPPED: test command not verified"
  fi
done
