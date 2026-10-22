cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

export PYTHONPATH="$PWD/artifacts/v1.168-max/maxserve_cta_extension:$PWD/artifacts/v1.168-max/maxserve_cta_extension/bootstrap:$PYTHONPATH"

python3 -c "import cta_scheduler_factory; print('CTA SCHEDULER FACTORY IMPORT: PASS')"
