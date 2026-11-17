cd /application1/sajjna8/redis_latency_test/jarvis_build

grep -oE 'REDIS_[A-Z_]+_MS' src/main/java/com/verizon/jarvis/repository/SessionRepository.java | sort | uniq -c
