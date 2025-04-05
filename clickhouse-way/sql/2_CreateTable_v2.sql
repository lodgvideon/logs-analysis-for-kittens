create table if not exists logs_table_v2
(
    timestamp    DateTime codec (Delta,ZSTD),
    duration     Float32 CODEC (ZSTD),
    remote_addr  String CODEC (ZSTD),
    resp_code    UInt32 codec (ZSTD),
    request_type LowCardinality(String) codec (ZSTD),
    path         LowCardinality(String) codec (ZSTD),
    useragent    LowCardinality(String) codec (ZSTD),
    params       String codec (ZSTD),
    request_body String codec (ZSTD),
    source_file  LowCardinality(String) codec (ZSTD),
    host         LowCardinality(String) codec (ZSTD),
    label        LowCardinality(String) default
                                            dictGetOrDefault(
                                                    'regexp_dict_api',
                                                    'tag',
                                                    concat(toString(resp_code), ' ', request_type, ' ', path,
                                                           if(params != '', concat('?', params), ''), request_body),
                                                    'Unknown'
                                            )
)
    engine = MergeTree
        PARTITION BY toStartOfInterval(timestamp, toIntervalHour(2))
        ORDER BY (timestamp);