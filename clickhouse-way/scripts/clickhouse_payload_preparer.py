import os
import re
import sys
import time
import traceback
import jsonline_generator
from datetime import datetime

import clickhouse_driver
from clickhouse_driver import Client

user_agent_re_pattern = '\((?P<info>.*?)\)(\s|$)|(?P<name>.*?)\/(?P<version>.*?)(\s|$)'
user_agent_compiled = re.compile(pattern=user_agent_re_pattern)


def is_user_agent(str):
    if user_agent_compiled.match(str):
        return True
    else:
        return False


def parse_cookies(cookie_string):
    """
    Парсит строку с куками в словарь.

    :param cookie_string: строка с куками (например, "key1=value1; key2=value2")
    :return: словарь с куками
    """
    cookies = {}
    # Разделяем строку по разделителю "; "
    for cookie in cookie_string.split('; '):
        # Разделяем каждую пару ключ=значение
        if '=' in cookie:
            key, value = cookie.split('=', 1)  # Только первое "="
            cookies[key.strip()] = value.strip()
    return cookies


def rfc3339_to_timestamp(rfc3339_string):
    """
    Конвертирует строку в формате RFC3339 в timestamp (количество секунд с эпохи Unix)

    Параметры:
    rfc3339_string (str): строка в формате RFC3339 (например, "2025-04-03T03:21:02Z")

    Возвращает:
    float: timestamp

    Поднимает:
    ValueError: если строка не соответствует формату RFC3339
    """

    # RFC3339 допускает несколько вариантов формата
    # Основной формат: "YYYY-MM-DDTHH:mm:ssZ"
    # Также может быть: "YYYY-MM-DDTHH:mm:ss.ffffffZ"

    try:
        # Пытаемся парсить с микросекундами
        dt = datetime.strptime(rfc3339_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            # Если не получилось, пробуем без микросекунд
            dt = datetime.strptime(rfc3339_string, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as e:
            raise ValueError("Неверный формат строки RFC3339") from e

    # Конвертируем в timestamp
    timestamp = time.mktime(dt.timetuple()) + dt.microsecond / 1e6

    return timestamp


def parse_datetime(date_string):
    """
    Конвертирует строку даты в формате 'YYYY-MM-DDTHH:MM:SS+00:00' в объект datetime

    Параметры:
    date_string (str): строка даты в формате '2025-03-31T21:15:18+00:00'

    Возвращает:
    datetime: объект datetime

    Поднимает:
    ValueError: если строка не соответствует формату
    """
    try:
        # Форматируем строку с учетом часового пояса
        dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")
        return dt
    except ValueError as e:
        raise ValueError("Неверный формат строки даты") from e


def unescape_json(escaped_json_str):
    """
    Преобразует строку с экранированными символами обратно в валидный JSON

    Параметры:
    escaped_json_str (str): строка с экранированными символами

    Возвращает:
    str: валидная JSON строка

    Поднимает:
    ValueError: если строка не может быть преобразована в валидный JSON
    """

    # Заменяем экранированные символы на нормальные
    cleaned_str = (
        escaped_json_str
        .replace('\\x22', '"')  # Заменяем \x22 на "
        .replace('\\\\', '\\')  # Восстанавливаем экранированные обратные слеши
    )
    return cleaned_str


def get_nginx_request(text):
    split = text.split('|')
    result = dict()

    try:
        #  request_body, source_file,
        #  host)
        result['timestamp'] = parse_datetime(split[2][1:][:-1].strip())
        if split[8] == '-':
            result['duration'] = 0
        else:
            result['duration'] = int(split[8])

        remote_chank = split[0].split(" ")
        result['remote_addr'] = remote_chank[5]

        result['resp_code'] = int(split[4])
        params = extract_request_params(split[3])
        result.update(params)

        result['useragent'] = split[7]

        # result['source_file'] =
        result['host'] = remote_chank[5]
        if split[9] != '-':
            try:
                result['request_body'] = unescape_json(
                    split[9].encode('ascii').decode('unicode_escape').encode('latin-1').decode('utf-8').strip())
            except Exception as ex:
                result['request_body'] = split[9]
        else:
            result['request_body'] = split[9]


    except Exception as ex:
        traceback.print_exc()
        print(ex)
        print("Erorr String Final:" + text)
        # print('parse exception', ex.with_traceback())

    return result


def extract_request_params(request):
    split = request.split('?', 1)
    result = dict()
    split_ = split[0]
    if split_.endswith('-'):
        split_ = split_[:-1]

    split__split = split_.split(' ')
    result['request_type'] = split__split[0]
    result['path'] = split__split[1]
    if len(split) > 1:
        result['params'] = "?" + split[1].split(" ")[0]
    else:
        result['params'] = ''
    return result


def nginx_row_reader(file_name):
    # line_cnt = 0
    basename = os.path.basename(file_name)
    with open(file_name, 'rb') as file:
        # with open(file_name, 'rb') as file:
        for line in file:
            request = get_nginx_request(line.decode("utf-8"))
            if len(request) < 10:
                print(f'PARSING ERROR:{line.decode("utf-8")}')
                continue
            request['source_file'] = basename

            yield (
                request['timestamp'],
                request['duration'],
                request['remote_addr'],
                request['resp_code'],
                request['request_type'],
                request['path'],
                request['useragent'],
                request['params'],
                request['request_body'],
                request['source_file'],
                request['host']
            )


class DataExtractor:
    client: clickhouse_driver.Client = None

    def __init__(self, client: clickhouse_driver.Client):
        self.client = client

    def get_profile(self, database: str, from_date: str, to_date: str):
        profile_query = f"""

        WITH counts_per_second AS (
            SELECT
                timestamp_second,
                request_type,
                label,

                countMerge(count) AS requests_count
            FROM {database}.logs_aggregated_by_second
            WHERE timestamp_second >=toDateTime('{from_date}')
              AND timestamp_second < toDateTime('{to_date}')
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
            """

        return self.client.execute(profile_query)

    def get_payload_for_tag_iter(self, database: str, request_type, label, quantity, from_date,
                                 to_date):
        sql = f'''

        select request_type, path, params, request_body, useragent
        from {database}.logs_table_v2
        where request_type = '{request_type}'
          and label = '{label}' and
              timestamp between '{from_date}' and '{to_date}'
              limit {quantity};
            '''
        return self.client.execute_iter(sql)


def main(args):
    # Вход файл со списком файлов для импорта
    # Получаем список импортированных файлов
    #


    from_date = '2025-03-20 10:00:00'
    to_date = '2025-04-20 10:00:00'

    print("Внимание! Используется следующий временной интервал - отредактируйте под свои данные:")
    print("FROM:"+from_date)
    print("FROM:"+to_date)

    target_host = "localhost"
    payload_file = args[1]
    host = args[2]
    port = args[3]
    database = args[4]
    user = args[5]
    password = args[6]

    # settings = {}
    settings = {
        'connect_timeout': 100000,
        'max_execution_time': 100000,
        'send_timeout': 10000,
        'receive_timeout': 10000,
        'max_rows_to_read': 300000,
        'send_receive_timeout': 10000,
        'session_timeout': 10000000,
        'socket_timeout': 100000
    }

    client = Client(host=host, user=user, send_receive_timeout=1000, connect_timeout=1000, password=password, port=port,
                    settings=settings, secure=False, verify=False, database=database, compression=False)

    extractor = DataExtractor(client)
    profile = extractor.get_profile(database, from_date, to_date)
    with open(payload_file, 'w') as file:
        for request_type, label, weight in profile:
            for chunk in extractor.get_payload_for_tag_iter(database, request_type, label, int(weight), from_date,
                                                            to_date):

                jsonline = jsonline_generator.Jsonline(target_host)
                jsonline.with_tag(request_type + ' ' + label)
                jsonline.with_method(chunk[0])
                jsonline.with_uri(chunk[1])
                jsonline.with_params(chunk[2])
                if not chunk[3].startswith('-'):
                    jsonline.with_body(chunk[3])
                jsonline.add_header("User-Agent", chunk[4])
                jsonline.add_header("Content-Type", 'application/json')
                file.write(jsonline.toJson())
                file.write('\n')
            file.flush()


if __name__ == '__main__':
    argv = sys.argv
    main(argv)
