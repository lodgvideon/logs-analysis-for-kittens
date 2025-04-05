
-- Создаем целевую таблицу для агрегированных данных - Запросы в секунду
CREATE TABLE logs_aggregated_by_second_hits
(
    timestamp_second DateTime,
    request_type     LowCardinality(String),
    label            LowCardinality(String),
    count            AggregateFunction(count, UInt8)
) ENGINE = AggregatingMergeTree()
      PARTITION BY toStartOfDay(timestamp_second)
      ORDER BY (timestamp_second, request_type, label);

-- Создаем материализованное представление для агрегации
CREATE MATERIALIZED VIEW logs_aggregated_by_second_hits_mv
    TO logs_aggregated_by_second_hits
AS
SELECT toStartOfSecond(subtractSeconds(toDateTime64(now(), 3), duration)) AS timestamp_second,
       request_type,
       label,
       countState(1)                                                      AS count
FROM logs_table_v2
GROUP BY timestamp_second,
         request_type,
         label;