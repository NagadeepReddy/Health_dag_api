cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

grep -nE 'torch\.load|load_state_dict|model_0_base|model_0_|def __init__|checkpoint' pipeline.py | head -40
