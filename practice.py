cd /application1/sajjna8/tfy_triton_work

D=aal_triton_stage/triton_repo/rt-aal-upg-leads-v1/1

mkdir -p "$D/encoder"

cp -R aal_triton_stage/encoder/. "$D/encoder/"

chmod -R a+rX "$D/encoder"

du -sh "$D/encoder"
ls -lh "$D/encoder"
