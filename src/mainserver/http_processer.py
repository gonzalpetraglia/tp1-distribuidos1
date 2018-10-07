from custom_exceptions import BadRequestError
from datetime import datetime
from lib.encoder import encode_request, MAX_MESSAGE_LENGTH_IN_BYTES, _encode_socket, encode_response, encode_client
import socket
from configs import FILESERVER_NAME, FILESERVER_PREFIX, RESPONSES_PORT, NUMBER_OF_FILESERVERS, FILESERVERS_PORTS, LOG_FORMAT, LOG_LEVEL
from hashlib import md5
import json
import uuid
import traceback
import  http_parser
import logging
import signal
import time

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(LOG_LEVEL)

def send_response_error(status_code, message, client_socket, request_uri, method, address, request_datetime):
    client_info = encode_client(client_socket, request_datetime, address)
    response_encoded = encode_response(client_info, status_code, json.dumps({"status": message}), request_uri, method)
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


def treat_message(parsed_request, client_socket, address, request_datetime):
    try:
        method = parsed_request['method']
        request_uri = parsed_request['request_uri']
        body = parsed_request['body'] if method in ['POST', 'PUT'] else None
        request_uri = request_uri + '/' + str(uuid.uuid4()) if method == 'POST' else request_uri
        fileserver_index = calculate_fileserver(request_uri)
        message = encode_request(encode_client(client_socket, request_datetime, address), method, request_uri, body)
        sock_fileserver = socket.socket()
        sock_fileserver.connect(get_fileserver_address(fileserver_index))
        sock_fileserver.sendall(message)
        sock_fileserver.close()
    except Exception:
        logger.error(traceback.format_exc())
        send_response_error(500, 'unknown_error', client_socket, request_uri, method, address, request_datetime)


def http_process(accepted_clients_queue):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    finish = False
    while not finish:
        try:
            logger.debug('Waiting for a new client')
            message = accepted_clients_queue.get()
            logger.debug('Read {}'.format(message))
            if message == 'END':
                finish = True
            else:
                time.sleep(5)
                sock, address = message    
                logger.info('Going to read from socket from new client')
                sock.settimeout(15)
                parsed_message = http_parser.read_http_message(lambda x: sock.recv(x).decode())
                treat_message(parsed_message, sock, address, datetime.now())
                sock.close()
        except socket.timeout as e:
            error_message = 'timedout'
            request_uri = 'couldnt_parse_uri'
            method = 'couldnt_parse_method'
            logger.warn('Timeout on read')
            send_response_error(400, error_message, sock, request_uri, method, address, datetime.now())
        except BadRequestError as e:
            error_message = e.get_error_message()
            request_uri = e.get_request_uri()
            method = e.get_method()
            logger.warn('Bad request: ' + error_message)
            send_response_error(400, error_message, sock, request_uri, method, address, datetime.now())
        except Exception as e:
            logger.error(traceback.format_exc())
            send_response_error(500, 'unknown_error', sock, "couldnt_parse_uri", "couldnt_parse_method", address, datetime.now())
    logger.info('Finished processing')