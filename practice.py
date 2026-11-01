find /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max \
-type f \( -name '*max*.py' -o -name '*fusion*.py' -o -name '*backend*.py' \) \
| grep -v __pycache__ | sort | head -60
