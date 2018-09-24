class BadRequestError(Exception):
    error_message = 'bad_request'
    def get_error_message(self):
        return self.error_message

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
