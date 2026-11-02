ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max
SOURCE="$ROOT/maxserve_bplan_extension/bplan_helper_weights_stage"
TARGET="$ROOT/bplan_helper_weights_stage"

if [ ! -f "$SOURCE/grecbase_integration_weights/fn_norm1_g.npy" ]; then
  echo "STOP: Source weight missing"
elif [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
  echo "STOP: Target already exists; preserving it"
else
  ln -s maxserve_bplan_extension/bplan_helper_weights_stage "$TARGET"
  test -f "$TARGET/grecbase_integration_weights/fn_norm1_g.npy" \
    && echo "BPLAN BATCH-2 WEIGHT PATH: PASS"
fi
