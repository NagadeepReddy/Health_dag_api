R=/application1/cta_max_native_release_candidate_20261028

echo "=== CTA ROUTER ==="
grep -nE 'ROUTES|APIType|register_cta_routes|/v2/cta|predict|add_api_route|route\(' \
  "$R/cta_router.py"

echo "=== NATIVE LAUNCHER REGISTRATION ==="
grep -nE 'register_cta_routes|api_server|run_module|TokenGeneratorPipeline' \
  "$R/cta_native_launcher.py"

echo "=== FINAL SERVER ROUTING LOG ==="
grep -iE 'route|endpoint|404|registered|server ready' \
  /application1/cta_native_faiss_live_test.log | tail -25

echo "CHECK COMPLETE — NO FILES MODIFIED"
