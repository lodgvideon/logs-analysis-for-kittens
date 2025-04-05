import json
from urllib import parse

GET = 'GET'
POST = 'POST'
PUT = 'PUT'
DELETE = 'DELETE'


class Jsonline:

    def __init__(self, host):
        self.headers = dict()
        self.cookies = dict()
        self.params = dict()
        self.url_encoded_params = dict()
        self.body = ''
        self.host = host


    def toJson(self):
        uri = self.uri
        if len(self.params) > 0:
            param_symbol = ''
            if '?' in self.uri:
                param_symbol = '&'
            uri += param_symbol + self.get_params_str()

        if self.body == '' and len(self.url_encoded_params) > 0:
            self.body = parse.urlencode(self.url_encoded_params)

        dumps = json.dumps(
            {"body": self.body, "headers": self.headers, "host": self.host, "tag": self.get_formatted_tag(),
             "method": self.method,
             "uri": uri}, ensure_ascii=False)
        return dumps

    def get_formatted_tag(self):
        tag: str = self.tag
        return tag

    def get_params_str(self):
        i = 0
        params_str = '?'
        if len(self.params) > 0:
            for key in self.params.keys():
                if i > 0:
                    params_str += '&' + key + '=' + self.params[key]
                else:
                    params_str += key + '=' + self.params[key]
                i = i + 1
        return params_str

    def with_tag(self, tag):
        self.tag = tag
        return self

    def with_body(self, body):
        self.body = body
        return self

    def add_header(self, key, value):
        self.headers[key] = value
        return self

    def add_cookie(self, key, value):
        if not 'cookie' in self.headers.keys():
            self.headers['cookie'] = f'{key}={value}'
        else:
            self.headers['cookie'] += f'; {key}={value}'
        return self

    def add_form_url_encoded_param(self, key, value):
        self.url_encoded_params[key] = value
        return self

    def with_method(self, method):
        self.method = method
        return self

    def with_uri(self, uri):
        self.uri = uri
        return self

    def with_params(self, params):
        if params != '':
            params_list = params.split('&')
            for param in params_list:
                if '=' in param:
                    param_tuple = param.split('=')
                    self.add_requests_param(param_tuple[0], param_tuple[1])

    def add_requests_param(self, param_key, param_value):
        self.params[param_key] = param_value
        return self
