long redisWriteStartNs = System.nanoTime();

stringRedisTemplate.opsForHash().put(
    readApplicationConfigValues.getCacheModelResponseHash()
        .concat(realTimeModelResponse.getInsightName())
        .concat(HYPHEN).concat(identifier),
    "INSIGHT_NAME",
    realTimeModelResponse.getInsightName());

logger.info("REDIS_WRITE_INSIGHT_NAME_MS={}",
    (System.nanoTime() - redisWriteStartNs) / 1_000_000.0);
