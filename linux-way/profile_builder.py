



def get_statistics_from_clickhouse(date_str):
    sql = f'''select max("count") as "max_in_hour",request_type,tag,max(duration) from (
                select count(*) as "count",sum(duration) as "duration",date_trunc('hour',timestamp),request_type,tag
                    from log_jira
                    where source_file = 'nginx' and date_trunc('day',timestamp) == '{date_str}' 
                    and username not in {ROBOTS_USERNAMES}
                    group by date_trunc('hour',timestamp),tag,request_type) group by request_type, tag   order by "max_in_hour" desc'''
    execute = client.execute(sql)
    statistics_map = dict(map((lambda row: (row[1] + ' ' + row[2], row[0])), execute))
    return statistics_map




def get_statistics_from_clickhouse_for_user(date_str, username):
    sql = f'''select max("count") as "max_in_hour",request_type,tag,max(duration) from (
                select count(*) as "count",sum(duration) as "duration",date_trunc('hour',timestamp),request_type,tag
                    from log_jira
                    where source_file = 'nginx' and date_trunc('day',timestamp) == '{date_str}'
                    and username = '{username}' 
                group by date_trunc('hour',timestamp),tag,request_type) group by request_type, tag   order by "max_in_hour" desc'''
    execute = client.execute(sql)
    statistics_map = dict(map((lambda row: (row[1] + ' ' + row[2], row[0])), execute))
    return statistics_map


# Для каждого тега - формируем запросы


def prepare_custom_requests(request_type, headers: list, sql, uri, add_x_username, mapping_fields):
    results = list()
    execute_iter = client.execute_iter(sql)
    i = 0
    row: tuple
    tag = f'{request_type} {uri}'
    for row in execute_iter:

        request = get_base_request()
        request.with_tag(tag)
        request.with_method(request_type)
        request.with_uri(uri)
        # default content-type
        request.add_header('Content-Type', 'application/json')
        for field in mapping_fields:
            if field[0] == 'body':
                body = row[field[1]]
                if body != '':
                    try:
                        json.loads(body)
                        request.add_header('Content-Type', 'application/json')
                    except Exception:
                        request.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
                    request.with_body(remove_attachment(body))
            if field[0] == 'params':
                request.with_params(row[field[1]])
            if field[0] == 'uri' or field[0] == 'path':
                request.with_uri(row[field[1]])
        # for everriding headers
        if headers:
            for header in headers:
                header_value = header[1]
                request.add_header(header[0], header_value)
        results.append(request.toJson())
        i += 1
    return results, i