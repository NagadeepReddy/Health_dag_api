long idWriteStartNs = System.nanoTime();

stringRedisTemplate.opsForHash().put(
    readApplicationConfigValues.getCacheModelResponseHash()
        .concat(realTimeModelResponse.getInsightName())
        .concat(HYPHEN).concat(identifier),
    "ID",
    identifier.trim());

logger.info("REDIS_WRITE_ID_MS={}",
    (System.nanoTime() - idWriteStartNs) / 1_000_000.0);
