from config import MAX_HEADER_LENGTH, MAX_BODY_LENGTH, VALID_POST_URI_REGEX, VALID_PUT_GET_DELETE_URI_REGEX, logger
from exceptions import BadRequestError, BodyTooLong, BodyNotJSON, MethodNotSupported, InvalidURI, MissingBody
import json
class RedefinedHeaderKey(Exception):
    pass

def parse_http_request_line(request_line):
    method, request_uri, http_version = request_line.split(" ") 
    return {
        "method": method,
        "request_uri": request_uri,
        "http_version": http_version
    }

def validate_request(parsed_request):
    method = parsed_request['method']
    request_uri = parsed_request['request_uri']

    content_length = int(parsed_request['headers'].get('content-length', 0))

    content_type = parsed_request['headers'].get('content-type', None)
    logger.info('Going to validate {} {} {} {}'.format(method, request_uri, content_length, content_type))

    if method not in ['POST', 'PUT', 'DELETE', 'GET']:
        raise MethodNotSupported()
    
    if (method in ['POST', 'PUT'] and not content_length):
        raise MissingBody()

    if (method in ['POST', 'PUT'] and  content_length > MAX_BODY_LENGTH):
        raise BodyTooLong()

    if (method in ['POST', 'PUT'] and (not content_type or 'application/json' not in content_type)):
        raise BodyNotJSON()
    
    if method == 'POST' and not VALID_POST_URI_REGEX.match(request_uri):
        raise InvalidURI()

    if method != 'POST' and not VALID_PUT_GET_DELETE_URI_REGEX.match(request_uri):
        raise InvalidURI()

def parse_http_headers(text):
    lines = text.splitlines() # TODO Handle errors
    parsed_message = parse_http_request_line(lines[0])
    parsed_message["headers"] = {}
    for line in lines[1:]:
        header_key, header_value = line.split(": ")
        if header_key in parsed_message:
            raise RedefinedHeaderKey(header_key)
        parsed_message["headers"][header_key.lower()] = header_value
    return parsed_message


def read_http_message(read):
    message = ''
    bytes_read = 0
    while '\r\n\r\n' not in message:
        if bytes_read > MAX_HEADER_LENGTH:
            raise Exception() # TODO change this
        chunk = read(2048)
        message += chunk
        bytes_read += len(chunk)


    headers, body_init = message.split('\r\n\r\n')


    parsed_message = parse_http_headers(headers)
    validate_request(parsed_message)

    if 'content-length' in parsed_message['headers']:
        body = body_init
        body_bytes_read = len(body_init)

        while body_bytes_read < int(parsed_message['headers']['content-length']):
            chunk = read(2048)
            body += chunk
            body_bytes_read += len(chunk)
        parsed_message["body"] = body
        
    return parsed_message
