cd /application1/sajjna8/tfy_triton_work

SRC=rt-aal-upg-lead-v1/artifacts/v1.4
DST=aal_triton_stage/triton_repo/rt-aal-upg-leads-v1/1

mkdir -p "$DST"/{config,core-artifact,utils/dependency-utils}

cp -R "$SRC/config/." "$DST/config/"
cp -R "$SRC/utils/dependency-utils/." "$DST/utils/dependency-utils/"

install -m 644 "$SRC/core-artifact/pipeline.py" \
  "$DST/core-artifact/pipeline.py"

for f in "$SRC"/core-artifact/{centile,decile}_*.txt; do
  install -m 644 "$f" "$DST/core-artifact/"
done

chmod -R u+rwX,go+rX "$DST/config" "$DST/utils" "$DST/core-artifact"

du -sh "$DST"
ls -lh "$DST/core-artifact/"
