long redisExpireStartNs = System.nanoTime();

stringRedisTemplate.expire(
    readApplicationConfigValues.getCacheModelResponseHash()
        .concat(realTimeModelResponse.getInsightName())
        .concat(HYPHEN).concat(identifier),
    Duration.ofSeconds(readApplicationConfigValues.getCacheModelResponseExpiryTime()));

logger.info("REDIS_EXPIRE_LATENCY_MS={}",
    (System.nanoTime() - redisExpireStartNs) / 1_000_000.0);
