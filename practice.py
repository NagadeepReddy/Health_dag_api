bash <<'SH'
set -euo pipefail

ARCHIVE=/application1/CTA_MAX_TEAM_HANDOFF_20261031.tar.gz
ROOT=CTA_MAX_TEAM_HANDOFF_STAGE_20261031

echo "=== VERIFY CHECKSUM ==="
(cd /application1 && sha256sum -c "$(basename "$ARCHIVE").sha256")

echo "=== VERIFY ARCHIVE CONTENTS ==="
tar -tzf "$ARCHIVE" | awk -v root="$ROOT" '
$0 == root "/run_cta_native.sh" { launcher=1 }
$0 == root "/TEAM_HANDOFF_README.txt" { readme=1 }
/\/real_max_batch2_backend.py$/ { backend=1 }
/\/cta_native_model\// { model=1 }
/\/cta_max\/sequence_weights\// { weights=1 }
/\/batch2\/cta_max\// { duplicate=1 }
/\.bak$|\.pyc$|\/__pycache__\// { junk=1 }
END {
  print "Launcher:", launcher ? "PASS" : "FAIL"
  print "README:", readme ? "PASS" : "FAIL"
  print "Backend:", backend ? "PASS" : "FAIL"
  print "Model:", model ? "PASS" : "FAIL"
  print "Weights:", weights ? "PASS" : "FAIL"
  print "Duplicate excluded:", duplicate ? "FAIL" : "PASS"
  print "Backup/cache excluded:", junk ? "FAIL" : "PASS"
  if (!launcher || !readme || !backend || !model || !weights || duplicate || junk) exit 1
}'

echo "FINAL ARCHIVE INTEGRITY: PASS"
SH
