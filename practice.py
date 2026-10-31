SRC=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max/sequence_weights
CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
DST="$CLEAN/artifacts/v1.168-max/cta_max/sequence_weights"

if [ ! -f "$SRC/fn_norm1_g.npy" ]; then
  echo "STOP: Original model weights missing"
elif [ ! -d "$CLEAN/artifacts/v1.168-max/cta_max" ]; then
  echo "STOP: Clean VM package not found"
else
  NEED=$(du -sk "$SRC" | awk '{print $1}')
  FREE=$(df -Pk "$CLEAN" | awk 'NR==2 {print $4}')

  if [ "$FREE" -le $((NEED * 2 + 1048576)) ]; then
    echo "STOP: Insufficient disk space"
  else
    mkdir -p "$DST"
    cp -an "$SRC"/. "$DST"/

    if diff -qr "$SRC" "$DST" >/dev/null; then
      echo "CLEAN VM MODEL WEIGHTS: PASS"
      echo "ORIGINAL DS CODE: UNCHANGED"
      echo "ORIGINAL WEIGHTS: UNCHANGED"
      echo "CONTAINERS RESTARTED: NONE"
    else
      echo "STOP: Clean model weights differ or are incomplete"
    fi
  fi
fi
