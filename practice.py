cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -RnE 'No expected 256-d|rotary.*(freq|weight)|freq.*rotary' \
  artifacts/v1.168-max/cta_max \
  artifacts/v1.168-max/run_live_max_inference.py \
  artifacts/v1.168-max/*sanity* 2>/dev/null | head -45
