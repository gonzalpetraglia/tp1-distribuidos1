from custom_exceptions import BadRequestError
from lib.encoder import encode_response, encode_request, decode_response, MAX_MESSAGE_LENGTH_IN_BYTES, encode_socket
import socket
from configs import FILESERVER_NAME, FILESERVER_PREFIX, RESPONSES_PORT, NUMBER_OF_FILESERVERS, FILESERVERS_PORTS, LOG_FORMAT, LOG_LEVEL
from hashlib import md5
import json
import uuid
import traceback
import  http_parser
import logging

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(LOG_LEVEL)

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
    responses_queue_socket.sendall(response_encoded)
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


def treat_message(parsed_request, client_socket):
    try:
        method = parsed_request['method']
        request_uri = parsed_request['request_uri']
        body = parsed_request['body'] if method in ['POST', 'PUT'] else None
        request_uri = request_uri + '/' + str(uuid.uuid4()) if method == 'POST' else request_uri
        fileserver_index = calculate_fileserver(request_uri)
        message = encode_request(client_socket, method, request_uri, body)
        sock_fileserver = socket.socket()
        sock_fileserver.connect(get_fileserver_address(fileserver_index))
        sock_fileserver.sendall(message)
        sock_fileserver.close()
    except Exception:
        logger.error(traceback.format_exc())
        send_response_error(500, 'unknown_error', client_socket, request_uri, method)


def http_process(accepted_clients_queue):
    while True:
        try:
            logger.debug('Waiting for a new client')
            sock, address = accepted_clients_queue.get()
            logger.info('Going to read from socket from new client')
            sock.settimeout(5)
            parsed_message = http_parser.read_http_message(lambda x: sock.recv(x).decode())
            treat_message(parsed_message, sock)
        except socket.timeout as e:
            error_message = 'timedout'
            request_uri = 'couldnt_parse_uri'
            method = 'coudlnt_parse_method'
            logger.warn('Timeout on read')
            send_response_error(400, error_message, sock, request_uri, method)
        except BadRequestError as e:
            error_message = e.get_error_message()
            request_uri = e.get_request_uri()
            method = e.get_method()
            logger.warn('Bad request: ' + error_message)
            send_response_error(400, error_message, sock, request_uri, method)
        except Exception as e:
            logger.error(traceback.format_exc())
            send_response_error(500, 'unknown_error', sock, "couldnt_parse_uri", "couldnt_parse_method")
