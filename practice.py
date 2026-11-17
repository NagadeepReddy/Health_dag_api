cd /application1/sajjna8/redis_latency_test/jarvis_build

grep -nE 'REDIS_(READ|WRITE|JSON|EXPIRE).*_MS' src/main/java/com/verizon/jarvis/repository/SessionRepository.java
