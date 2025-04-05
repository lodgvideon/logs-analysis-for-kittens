create table if not exists logs_table_v1
(
    timestamp    DateTime codec (Delta,ZSTD),
    duration     UInt32,
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
                                            multiIf(
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET /search'),
                                                    'GET /search',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET /about'),
                                                    'GET /about',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), '') || ' ' ||
                                                          request_body, '^POST /post.*[aA]ction1'),
                                                    'POST /post (Action1)',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), '') || ' ' ||
                                                          request_body, '^POST /post.*[aA]ction2'),
                                                    'POST /post (Action2)',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), '') || ' ' ||
                                                          request_body, '^POST /post.*[aA]ction3'),
                                                    'POST /post (Action3)',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), '') || ' ' ||
                                                          request_body, '^POST /post'), 'POST /post',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET /profile/'),
                                                    'GET /profile/{user}',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET /product/'),
                                                    'GET /product/{productId}',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET / '),
                                                    'GET / ',
                                                    'other'
                                            )
)
    engine = MergeTree
        PARTITION BY toStartOfInterval(timestamp, toIntervalHour(2))
        ORDER BY (timestamp);