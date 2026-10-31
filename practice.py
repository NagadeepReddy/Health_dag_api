ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
SRC="$ROOT/batch2/cta_max/nlp_weights"
DST="$ROOT/artifacts/v1.168-max/cta_max/nlp_weights"

if [ -f "$SRC/nlp_encoder.embeddings.word_embeddings.weight.npy" ] &&
   [ -d "$SRC" ] &&
   [ ! -e "$DST" ] &&
   [ ! -L "$DST" ] &&
   [ "$(df -Pk "$(dirname "$DST")" | awk 'NR==2 {print $4}')" -gt "$(du -sk "$SRC" | awk '{print $1}')" ]; then

  cp -a "$SRC" "$DST" &&
  diff -qr "$SRC" "$DST" &&
  echo "CLEAN NLP WEIGHTS: PASS"
else
  echo "STOP: Source, destination, or disk precheck failed"
fi
