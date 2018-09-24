from exceptions import BadRequestError, BodyTooLong, BodyNotJSON, MethodNotSupported, InvalidURI, MissingBody
from lib.encoder import encode_response, encode_request, decode_response, MAX_MESSAGE_LENGTH_IN_BYTES, encode_socket
import socket
from config import FILESERVER_NAME, FILESERVER_PREFIX, RESPONSES_PORT, NUMBER_OF_FILESERVERS, FILESERVERS_PORTS, VALID_POST_URI_REGEX, VALID_PUT_GET_DELETE_URI_REGEX
from hashlib import md5
import json
import logging
import uuid
import traceback
import  http_parser


FORMAT = "%(asctime)-15s %(process)d %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(logging.DEBUG)

def send_response_error(status_code, message, client_socket, request_uri, method):
    response_dict = {
        "status_code": status_code,
        "body": json.dumps({"status": message}),
        "client": encode_socket(client_socket),
        "request_uri": request_uri,
        "method": method
    }
    response_encoded = encode_response(response_dict)
    responses_queue_socket = socket.socket()
    responses_queue_socket.connect(('127.0.0.1', RESPONSES_PORT))
    responses_queue_socket.send(response_encoded)
    responses_queue_socket.close()

def calculate_fileserver(URI_postfix):
    return int(md5(URI_postfix.encode()).hexdigest(), 16) % NUMBER_OF_FILESERVERS + 1

def get_fileserver_address(fileserver_index):
    if FILESERVER_NAME: # Intended for localhost tests
        fileserver_name = FILESERVER_NAME
    else:
        fileserver_name = FILESERVER_PREFIX + str(fileserver_index)
    logger.debug('FILESERVER: {}:{}'.format(fileserver_name, FILESERVERS_PORTS))
    return fileserver_name, FILESERVERS_PORTS


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

    if (method in ['POST', 'PUT'] and  content_length > MAX_MESSAGE_LENGTH_IN_BYTES):
        raise BodyTooLong()

    if (method in ['POST', 'PUT'] and (not content_type or 'application/json' not in content_type)):
        raise BodyNotJSON()
    
    if method == 'POST' and not VALID_POST_URI_REGEX.match(request_uri):
        raise InvalidURI()

    if method != 'POST' and not VALID_PUT_GET_DELETE_URI_REGEX.match(request_uri):
        raise InvalidURI()


def treat_message(msg, client_socket):
    try:
        parsed_request = http_parser.parse_http(msg)
        method = parsed_request['method']
        request_uri = parsed_request['request_uri']
        validate_request(parsed_request)

        body = parsed_request['body'] if method in ['POST', 'PUT'] else None
        request_uri = request_uri + '/' + str(uuid.uuid4()) if method == 'POST' else request_uri
        fileserver_index = calculate_fileserver(request_uri)
        message = encode_request(client_socket, method, request_uri, body)
        sock_fileserver = socket.socket()
        sock_fileserver.connect(get_fileserver_address(fileserver_index))
        sock_fileserver.send(message)
        sock_fileserver.close()
    except BadRequestError as e:
        error_message = e.get_error_message()
        logger.warn('Bad request: ' + error_message)
        send_response_error(400, error_message, client_socket, request_uri, method)
    except Exception:
        logger.error(traceback.format_exc())
        send_response_error(500, 'unknown_error', client_socket, request_uri, method)


def http_process(accepted_clients_queue):
    while True:
        try:
            logger.debug('Waiting for a new client')
            sock, address = accepted_clients_queue.get()
            chunk  = '' # TODO Dont have everything on memory
            breaks_found = 0
            logger.info('Going to read from socket from new client')
            chunk += sock.recv(2048).decode()
            treat_message(chunk, sock)

        except Exception:
            logger.error(traceback.format_exc())
            send_response_error(500, 'unknown_error', sock, "couldnt_parse_uri", "couldnt_parse_method")
