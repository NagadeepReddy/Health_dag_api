BASE=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max
SRC="$BASE/sequence_weights"
ALIAS="$BASE/grecbase_integration_weights"

if [ ! -f "$SRC/seq_dense_weight.npy" ]; then
  echo "STOP: Source weight missing"
elif [ -L "$ALIAS" ]; then
  echo "WEIGHT DIRECTORY LINK: ALREADY PRESENT"
elif [ -e "$ALIAS" ]; then
  echo "STOP: Existing directory must be preserved"
else
  ln -s sequence_weights "$ALIAS" || exit 1
  echo "WEIGHT DIRECTORY LINK: CREATED"
fi

if [ -f "$ALIAS/seq_dense_weight.npy" ]; then
  echo "DENSE WEIGHT LOOKUP: PASS"
  echo "CLEAN PACKAGE: PORTABLE RELATIVE LINK"
  echo "ORIGINAL DS CODE: UNCHANGED"
  echo "CONTAINERS RESTARTED: NONE"
else
  echo "DENSE WEIGHT LOOKUP: FAIL"
fi
