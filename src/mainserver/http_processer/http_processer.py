from datetime import datetime
import socket
import json
import uuid
import traceback
import logging
import signal
import time

from http_processer.http_parser import read_http_message
from configs import FILESERVER_NAME, FILESERVER_PREFIX, RESPONSES_PORT, NUMBER_OF_FILESERVERS, FILESERVERS_PORTS, LOG_FORMAT, LOG_LEVEL
from custom_exceptions import BadRequestError
from lib.response_communicator import communicate_response
from lib.request_communicator import communicate_request
from lib.encoder import encode_client

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(LOG_LEVEL)

def send_response_error(status_code, message, client_socket, request_uri, method, address, request_datetime):
    client_info = encode_client(client_socket, request_datetime, address)
    communicate_response(client_info, status_code, json.dumps({"status": message}), request_uri, method, '127.0.0.1', RESPONSES_PORT)
    

def treat_message(parsed_request, client_socket, address, request_datetime):
    try:
        method = parsed_request['method']
        request_uri = parsed_request['request_uri']
        body = parsed_request['body'] if method in ['POST', 'PUT'] else None
        request_uri = request_uri + '/' + str(uuid.uuid4()) if method == 'POST' else request_uri
        client = encode_client(client_socket, request_datetime, address)
        communicate_request(client, method, request_uri, body)
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
                sock, address = message    
                logger.info('Going to read from socket from new client')
                sock.settimeout(5)
                parsed_message = read_http_message(lambda x: sock.recv(x).decode())
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