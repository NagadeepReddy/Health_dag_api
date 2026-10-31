PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-clean-batch2-http-20261030"

AVAILABLE=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
if [ "$AVAILABLE" -lt 18874368 ]; then
  echo "STOP: Insufficient available RAM"
else
  $PODMAN start "$NAME" &&
  $PODMAN exec "$NAME" /bin/sh -c '
    for f in nlp_bert_max.py sequence_pooling_max.py; do
      p="/workspace/artifacts/v1.168-max/cta_max/$f"
      if [ -f "$p" ]; then
        echo "PASS: $f"
      else
        echo "STOP: Missing $f"
        exit 1
      fi
    done
    echo "CLEAN CONTAINER READY: PASS"
  '
fi
