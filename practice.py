long jsonStartNs = System.nanoTime();

String modelResponseJson =
    objectMapper.writeValueAsString(realTimeModelResponse);

logger.info("REDIS_JSON_SERIALIZATION_MS={}",
    (System.nanoTime() - jsonStartNs) / 1_000_000.0);

long modelWriteStartNs = System.nanoTime();

stringRedisTemplate.opsForHash().put(
    readApplicationConfigValues.getCacheModelResponseHash()
        .concat(realTimeModelResponse.getInsightName())
        .concat(HYPHEN).concat(identifier),
    "MODEL_RESPONSE",
    modelResponseJson);

logger.info("REDIS_WRITE_MODEL_RESPONSE_MS={}",
    (System.nanoTime() - modelWriteStartNs) / 1_000_000.0);
