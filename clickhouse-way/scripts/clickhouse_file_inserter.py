import gzip
import os
import re
import sys
import time
import traceback
from datetime import datetime

import clickhouse_driver
import regex
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
        if  split[9] !='-':
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


def main(args):
    # Вход файл со списком файлов для импорта
    # Получаем список импортированных файлов
    #
    file = args[1]
    host = args[2]
    port = args[3]
    database = args[4]
    table = args[5]
    user = args[6]
    password = args[7]
    # insert_block_size = args[7]

    # settings = {}
    settings = {"insert_block_size": 300000,
                'connect_timeout': 100000,
                'max_execution_time': 100000,
                'send_timeout': 10000,
                'receive_timeout': 10000,
                'send_receive_timeout': 10000,
                'session_timeout': 10000000,
                'socket_timeout': 100000, }

    client = Client(host=host, user=user, send_receive_timeout=1000, connect_timeout=1000, password=password, port=port,
                    settings=settings, secure=False, verify=False, database=database, compression=False)

    # file = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(file):
        # print(file)

        print(f'Processing file: {file}')
        st = time.time()
        batch = []
        query =f"""
        INSERT INTO {database}.{table} 
            (timestamp,duration,remote_addr,resp_code,request_type,path,useragent,params,request_body,source_file,host)
            values 
            """

        batch = []
        for line in nginx_row_reader(file):
            batch.append(line)
            if len(batch) >= settings['insert_block_size']:
                try:
                    client.execute(query, batch, settings=settings)
                    batch = []

                except BaseException as ex:
                    traceback.print_exc()
                    print(f'File: {file} Proceeded with exception {ex}')
                    status = 0

        client.execute(query, batch, settings=settings)

        et = time.time()
        elapsed_time = et - st
        print(f'File: {file} took:', elapsed_time, 'seconds')
        print('Finish')


if __name__ == '__main__':
    argv = sys.argv
    main(argv)
