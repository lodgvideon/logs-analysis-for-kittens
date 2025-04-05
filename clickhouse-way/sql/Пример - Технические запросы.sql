
-- select * from system.mutations;;
-- Выисляет Размер таблицы в пожатом/непожатом виде
SELECT formatReadableSize(sum(data_compressed_bytes))                      AS compressed_size,
       formatReadableSize(sum(data_uncompressed_bytes))                    AS uncompressed_size,
       round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) AS ratio
FROM system.columns
WHERE table = 'logs_table_v2';

-- Выисляет Размер таблицы в пожатом/непожатом виде
SELECT formatReadableSize(sum(data_compressed_bytes))                      AS compressed_size,
       formatReadableSize(sum(data_uncompressed_bytes))                    AS uncompressed_size,
       round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) AS ratio
FROM system.columns
WHERE table = 'logs_table_v2';

--Вычисляет размер столбцов в пожатом/непожатом виде
SELECT name,
       formatReadableSize(sum(data_compressed_bytes))                      AS compressed_size,
       formatReadableSize(sum(data_uncompressed_bytes))                    AS uncompressed_size,
       round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) AS ratio
FROM system.columns
WHERE table = 'log_site_api'
GROUP BY name
ORDER BY sum(data_compressed_bytes) DESC;

-- Вычисляет кардинальность параметров.
select params, count()
from (select * from logs_table_v2 limit 10000000)
group by params
order by count() desc
limit 100;

