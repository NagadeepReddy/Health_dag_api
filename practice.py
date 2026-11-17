long createdDateStartNs = System.nanoTime();

stringRedisTemplate.opsForHash().put(
    readApplicationConfigValues.getCacheModelResponseHash()
        .concat(realTimeModelResponse.getInsightName())
        .concat(HYPHEN).concat(identifier),
    "CREATED_DATE",
    String.valueOf(timestamp.toInstant()));

logger.info("REDIS_WRITE_CREATED_DATE_MS={}",
    (System.nanoTime() - createdDateStartNs) / 1_000_000.0);
