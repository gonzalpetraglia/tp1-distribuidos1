import socket
import time
from multiprocessing import Process, Queue, Manager
from threading import Thread
import http_parser
import pickle
from hashlib import md5
import json
from lib.encoder import encode_response, encode_request, decode_response, MAX_MESSAGE_LENGTH_IN_BYTES, encode_socket
import uuid
import traceback
import logging
import os
from datetime import datetime
from config import NUMBER_OF_FILESERVERS, NUMBER_OF_FILESERVERS, NUMBER_OF_RESPONDERS, NUMBER_OF_PROCESSERS, REQUESTS_PORT, RESPONSES_PORT, VALID_POST_URI_REGEX, VALID_PUT_GET_DELETE_URI_REGEX, STATUS_CODE_MESSAGES, FILESERVERS_PORTS, FILESERVER_NAME, FILESERVER_PREFIX, LOGFILE
from exceptions import BadRequestError, BodyTooLong, BodyNotJSON, MethodNotSupported, InvalidURI, MissingBody



FORMAT = "%(asctime)-15s %(process)d %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(logging.DEBUG)
logger.info("Mainserver is up and running :)")

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


def send_log(queue, method, status_code, request_uri):
    queue.put({
        "method": method,
        "status_code": status_code,
        "request_uri": request_uri
    })

def http_respond(incoming_fileserver_responses_socket, logs_queue):
    try:
        while True:
            fileserver_response_socket, address = incoming_fileserver_responses_socket.accept()
            response_length_encoded = fileserver_response_socket.recv(8)
            response_length = int.from_bytes(response_length_encoded, byteorder='big', signed=True)

            response = fileserver_response_socket.recv(response_length)
            client_socket, status_code, body, request_uri, method = decode_response(response)
            logger.info('Going to respond {} {} {}'.format(method, request_uri, status_code))

            status_code_message = STATUS_CODE_MESSAGES[status_code]
            http_response = 'HTTP/1.1 {} {}\n'.format(status_code, status_code_message) + \
                            'Date: {}\n'.format(datetime.utcnow())+\
                            'Server: JSON-SERVER v1.0.0\n'+\
                            'Last-Modified: Wed, 22 Jul 2009 19:15:56 GMT\n'+\
                            'Content-Length: {}\n'.format(len(body)+2)+\
                            'Content-Type: application/json\n'+\
                            'Connection: Closed\n\n'+\
                            '{}\n\n'.format(body)
            client_socket.send(http_response.encode())
            logger.info("Done responding user, going to close the socket")
            client_socket.close()
            send_log(logs_queue, method, status_code, request_uri)
    except Exception:
        logger.error(traceback.format_exc())
        http_response = 'HTTP/1.1 {} {}\n'.format(500, "Internal Error") + \
                        'Date: {}\n'.format(datetime.utcnow())+\
                        'Server: JSON-SERVER v1.0.0\n'+\
                        'Last-Modified: Wed, 22 Jul 2009 19:15:56 GMT\n'+\
                        'Content-Length: {}\n'.format(len('{"status": "unknown_error"}'))+\
                        'Content-Type: application/json\n'+\
                        'Connection: Closed\n\n'+\
                        '{"status": "unknown_error"}'
        client_socket.send(http_response.encode())
        logger.info("Done responding user, going to close the socket")
        client_socket.close()
    incoming_fileserver_responses_socket.close()


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

def log_loop(logs_queue):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, 'a') as logfile:
        while True:
            try:
                log_dict = logs_queue.get()
                method = log_dict['method']
                request_uri = log_dict['request_uri']
                status_code = log_dict['status_code']

                logfile.write("{} {} {}\n".format(method, request_uri, status_code))
                logfile.flush()
            except Exception:
                logger.error(traceback.format_exc())

if __name__ == "__main__":
    accepted_clients_queue = Queue()
    logs_queue = Queue()



    fileserver_responses_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    fileserver_responses_socket.bind(('0.0.0.0', RESPONSES_PORT))
    fileserver_responses_socket.listen(5)


    processers = [Process(target=http_process, args=(accepted_clients_queue,)) for i in range(NUMBER_OF_PROCESSERS)]
    responders = [Process(target=http_respond, args=(fileserver_responses_socket, logs_queue,)) for i in range(NUMBER_OF_RESPONDERS)]
    logger_process = Process(target=log_loop, args=(logs_queue,))

    logger.info("Going to start {} processers and {} responders ".format(NUMBER_OF_PROCESSERS, NUMBER_OF_RESPONDERS))

    for processer in processers:
        processer.start()
    for responder in responders:
        responder.start()
    logger_process.start()


    incoming_clients_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    incoming_clients_socket.bind(('0.0.0.0', REQUESTS_PORT))
    incoming_clients_socket.listen(5)

    while True:
        logger.debug('Listening for more clients')

        accepted_client = incoming_clients_socket.accept()
        logger.info('Accepted new client')
        accepted_clients_queue.put(accepted_client)

    for processer in processers:
        processer.join()
    for responder in responders:
        responder.join()
    logger_process.join()

