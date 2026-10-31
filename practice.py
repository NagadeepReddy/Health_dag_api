podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /bin/sh -c '
for p in /proc/[0-9]*; do
  cmd=$(tr "\000" " " < "$p/cmdline" 2>/dev/null)
  case "$cmd" in
    *python*|*maxserve*)
      echo "PID: ${p##*/}"
      echo "CMD: ${cmd:0:180}"
      if test -r "$p/root/batch2/cta_max/grecbase_integration_weights/seq_dense_weight.npy"; then
        echo "WORKER WEIGHT ACCESS: PASS"
      else
        echo "WORKER WEIGHT ACCESS: FAIL"
      fi
      ;;
  esac
done
'
