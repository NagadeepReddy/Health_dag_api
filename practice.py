cd /application1/sajjna8/rt-pzaas-cta-offers-v1

if [ -f artifacts/v1.168-max/cta_native_model/arch.py ]; then
  sed -n '1,110p' artifacts/v1.168-max/cta_native_model/arch.py
else
  echo "CTA ARCH.PY MISSING — registration not complete"
fi
