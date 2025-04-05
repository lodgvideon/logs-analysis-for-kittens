-- Пример скрипта для запроса по Материальному представлению
SELECT
    timestamp_second,
    request_type,
    label,
    countMerge(count) AS count
FROM logs_aggregated_by_second
GROUP BY
    timestamp_second,
    request_type,
    label
ORDER BY
    timestamp_second,
    request_type,
    label;
