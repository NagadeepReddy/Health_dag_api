cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

SOURCE="$PWD/artifacts/v1.168-max/cta_max/grecbase_integration_weights"
BASE=/application1/cta_max_true_batch_dev_20261028
TARGET="$BASE/cta_max/grecbase_integration_weights"

CONTAINER_SOURCE=/workspace/artifacts/v1.168-max/cta_max/grecbase_integration_weights

if [ ! -f "$SOURCE/att_pooling.rotary_emb.inv_freq.npy" ]; then
  echo "STOP: Original rotary weight missing"
elif [ ! -d "$BASE/cta_max" ]; then
  echo "STOP: Batch MAX directory missing"
elif [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
  echo "STOP: Target already exists; preserve it"
else
  ln -s "$CONTAINER_SOURCE" "$TARGET" || exit 1

  echo "ROTARY WEIGHT LINK: CREATED"
  echo "SOURCE WEIGHT: PRESERVED"
  echo "TARGET: $TARGET"
  echo "CONTAINER SOURCE: $CONTAINER_SOURCE"
  echo "DS CODE: UNCHANGED"
  echo "MAX STARTUP: NOT PERFORMED"
fi
