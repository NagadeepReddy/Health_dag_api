ROOT=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031

if [ ! -d "$ROOT" ]; then
  echo "STOP: Handoff folder missing"
elif ! command -v setfacl >/dev/null; then
  echo "STOP: setfacl unavailable"
else
  setfacl -m u:sajjna8:--x /application1 &&
  setfacl -R -m u:sajjna8:rX "$ROOT" &&
  echo "NORMAL SSH READ ACCESS: PASS"
fi
