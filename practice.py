cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

PYTHONPATH="$PWD/artifacts/v1.168-max" \
python3 -c "import maxserve_cta_extension.cta_scheduler_factory; print('CTA FACTORY PACKAGE IMPORT: PASS')"
