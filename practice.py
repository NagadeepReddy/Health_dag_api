SRC=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_max
DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

if [ -e "$DST" ]; then
  echo "STOP: BPLAN MAX development folder already exists"
else
  mkdir -p "$DST" &&
  find "$SRC" -maxdepth 1 -type f -name '*.py' \
    -exec cp -n -t "$DST" {} + &&
  echo "BPLAN MAX SOURCE COPY: PASS" &&
  find "$DST" -maxdepth 1 -name '*.py' -printf '%f\n' | sort
fi
