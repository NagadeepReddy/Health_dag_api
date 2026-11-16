long redisReadStartNs = System.nanoTime();

Map<String, String> rowData = hashOperations.entries(readApplicationConfigValues.getCacheModelResponseHash().concat(insightName).concat(HYPHEN).concat(id));

logger.info("REDIS_READ_LATENCY_MS={}",
    (System.nanoTime() - redisReadStartNs) / 1_000_000.0);
