-- Пример скрипта для рассчета профиля нагрузки
WITH counts_per_second AS (
    SELECT
        timestamp_second,
        request_type,
        label,

        countMerge(count) AS requests_count
    FROM logs_aggregated_by_second
    WHERE timestamp_second >=toDateTime('2025-03-20 10:00:00')
      AND timestamp_second < toDateTime('2025-04-20 10:00:00')
    GROUP BY
        timestamp_second,
        request_type,
        label
)
SELECT
    request_type,
    label,
    quantile(0.95)(requests_count) AS p95_requests_per_second
FROM counts_per_second
GROUP BY
    request_type,
    label
ORDER BY
    request_type,
    label;