bash <<'SH'
set -euo pipefail

ROOT=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
OUT=/application1/CTA_MAX_TEAM_HANDOFF_20261031.tar.gz
TMP="${OUT}.partial.$$"

test -d "$ROOT" && test ! -e "$OUT" || {
  echo "STOP: Stage missing or archive already exists"
  exit 1
}

trap 'rm -f "$TMP"' EXIT

bash "$ROOT/run_cta_native.sh" check

if find "$ROOT" -type l -print -quit | grep -q .; then
  echo "STOP: Unreviewed symlinks remain"
  exit 1
fi

cat > "$ROOT/TEAM_HANDOFF_README.txt" <<'EOF'
CTA Offers Modular MAX Serve — CPU Batch-2

Validated: isolated startup, native HTTP 200, CTA JSON.
Original DS code and model behavior preserved.

Prerequisites:
- Linux, Podman, sufficient CPU/RAM
- Compatible MAX + FAISS runtime image
- Approximately 18 GiB available host RAM before launch

Check:
  bash ./run_cta_native.sh check

Start:
  export CTA_IMAGE=<team-approved-image>
  bash ./run_cta_native.sh start

Optional:
  CTA_PORT, CTA_CONTAINER_NAME,
  PODMAN_ROOT, PODMAN_RUNROOT

Other models:
- Shared MAX serving infrastructure is reusable.
- Matching architectures may reuse the adapter.
- Different architectures/contracts require model-specific adapters.
- Multi-model plug-and-play support is not yet validated.

Image approval and deployment on another VM remain
the receiving team's validation steps.
EOF

tar -C /application1 \
  --exclude='*/__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.bak' \
  --exclude='*.log' \
  --exclude='*/.git' \
  -czf "$TMP" \
  CTA_MAX_TEAM_HANDOFF_STAGE_20261031

tar -tzf "$TMP" |
  grep -F 'CTA_MAX_TEAM_HANDOFF_STAGE_20261031/run_cta_native.sh'

mv "$TMP" "$OUT"
sha256sum "$OUT" > "$OUT.sha256"

echo "TEAM HANDOFF ARCHIVE: PASS"
du -sh "$OUT"
echo "PACKAGE: $OUT"
echo "ORIGINAL RUNNING CODE: UNCHANGED"
SH
