class BadRequestError(Exception):

    error_message = 'bad_request'

    def __init__(self, method=None, request_uri=None):
        self.method = method
        self.request_uri = request_uri

    def get_error_message(self):
        return self.error_message

    def get_method(self):
        return self.method or 'couldnt_parse_method'
        
    def get_request_uri(self):
        return self.request_uri or 'couldnt_parse_request_error'

class HeaderTooLong(BadRequestError):
    error_message = 'header_too_long'

class RedefinedHeaderKey(BadRequestError):
    error_message = 'redefined_header_key'

class MalformedRequestLine(BadRequestError):
    error_message = 'malformed_request_line'

class BodyTooLong(BadRequestError):
    error_message = 'body_too_long'

class BodyNotJSON(BadRequestError):
    error_message = 'body_not_json'

class InvalidURI(BadRequestError):
    error_message = 'invalid_uri'

class MethodNotSupported(BadRequestError):
    error_message = 'method_not_supported'

class MissingBody(BadRequestError):
    error_message = 'missing_body'
