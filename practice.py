find /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168 -maxdepth 5 -type f \( -name 'model.py' -o -name 'models.py' -o -name 'pipeline.py' \) -printf '%p\n' | sort
