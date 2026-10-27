cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
f=artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py
if grep -q 'supported_encodings=' "$f"; then
  echo "Already configured; no changes made"
else
  sed -i '/default_encoding=SupportedEncoding.float32,/a\        supported_encodings={SupportedEncoding.float32},' "$f"
fi
grep -nE 'default_encoding|supported_encodings' "$f"
