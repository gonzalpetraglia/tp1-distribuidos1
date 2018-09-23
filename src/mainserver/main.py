import socket
import time
from multiprocessing import Process, Queue
from threading import Thread
import http_parser
import pickle
from hashlib import md5
import os
import re
import json
from lib.encoder import encode_response, encode_request, decode_response, MAX_MESSAGE_LENGTH_IN_BYTES, encode_socket
import uuid
import traceback
from datetime import datetime

NUMBER_OF_FILESERVERS = int(os.environ['NUMBER_OF_FILESERVERS'])
NUMBER_OF_RESPONDERS = int(os.environ.get('NUMBER_OF_RESPONDERS', 10))
NUMBER_OF_PROCESSERS = int(os.environ.get('NUMBER_OF_PROCESSERS', 10))
REQUESTS_PORT = int(os.environ.get('REQUESTS_PORT', 8080))
RESPONSES_PORT = int(os.environ.get('RESPONSES_PORT', 8090))
VALID_POST_URI_REGEX = re.compile('^/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$')
VALID_PUT_GET_DELETE_URI_REGEX = re.compile('^/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$')
STATUS_CODE_MESSAGES = {
    200: "OK",
    400: "Bad Request",
    500: "Internal Error",
    404: "Not Found"
}



class BodyTooLong(Exception):
    pass

class BodyNotJSON(Exception):
    pass

class InvalidURI(Exception):
    pass

class MethodNotSupported(Exception):
    pass

class MissingBody(Exception):
    pass


def send_response_error(status_code, message, client_socket):
    response_dict = {
        "status_code": status_code,
        "body": json.dumps({"status": message}),
        "client": encode_socket(client_socket)
    }
    response_encoded = encode_response(response_dict)
    responses_queue_socket = socket.socket()
    responses_queue_socket.connect(('127.0.0.1', RESPONSES_PORT))
    responses_queue_socket.send(response_encoded)
    responses_queue_socket.close()

def calculate_fileserver(URI_postfix):
    return int(md5(URI_postfix.encode()).hexdigest(), 16) % NUMBER_OF_FILESERVERS

def get_fileserver_address(fileserver_index):
    return '127.0.0.1', 9000 + fileserver_index

def validate_request(parsed_request):
    method = parsed_request['method']

    if method not in ['POST', 'PUT', 'DELETE', 'GET']:
        raise MethodNotSupported()
    
    content_length = int(parsed_request['headers'].get('content-length', 0))

    content_type = parsed_request['headers'].get('content-type', None)
    print (method, content_length, content_type)
    if (method in ['POST', 'PUT'] and not content_length):
        raise MissingBody()

    if (method in ['POST', 'PUT'] and  content_length > MAX_MESSAGE_LENGTH_IN_BYTES):
        raise BodyTooLong()

    if (method in ['POST', 'PUT'] and (not content_type or 'application/json' in content_type)):
        raise BodyNotJSON()

    request_uri = parsed_request['request_uri']
    
    if method == 'POST' and not VALID_POST_URI_REGEX.match(request_uri):
        raise InvalidURI()

    if method != 'POST' and not VALID_PUT_GET_DELETE_URI_REGEX.match(request_uri):
        raise InvalidURI()


def treat_message(msg, client_socket):
    try:
        # print(msg)
        parsed_request = http_parser.parse_http(msg)
        validate_request(parsed_request)
        method = parsed_request['method']
        
        body = parsed_request['body'] if method in ['POST', 'PUT'] else None
        parsed_request['request_uri'] = parsed_request['request_uri'] + '/' + str(uuid.uuid4()) if method == 'POST' else parsed_request['request_uri']
        fileserver_index = calculate_fileserver(parsed_request['request_uri'])
        message = encode_request(client_socket, parsed_request["method"], parsed_request["request_uri"], body)

        sock_fileserver = socket.socket()
        sock_fileserver.connect(get_fileserver_address(fileserver_index))
        sock_fileserver.send(message)
        sock_fileserver.close()
    except BodyTooLong:
        send_response_error(400, 'body_too_long', client_socket)
    except BodyNotJSON:
        send_response_error(400, 'body_not_json', client_socket)
    except MethodNotSupported:
        send_response_error(400, 'method_not_supported', client_socket)
    except InvalidURI:
        send_response_error(400, 'invalid_uri', client_socket)
    except MissingBody:
        send_response_error(400, 'missing_body', client_socket)
    except Exception:
        print (traceback.format_exc())
        send_response_error(500, 'unknown_error', client_socket)


def http_respond(incoming_fileserver_responses_socket):
    fileserver_response_socket, address = incoming_fileserver_responses_socket.accept()
    response_length_encoded = fileserver_response_socket.recv(8)
    response_length = int.from_bytes(response_length_encoded, byteorder='big', signed=True)
    # print (response_length)

    response = fileserver_response_socket.recv(response_length)
    client_socket, status_code, body = decode_response(response)
    status_code_message = STATUS_CODE_MESSAGES[status_code]
    # sockets_to_be_closed.put(client_socket)
    http_response = 'HTTP/1.1 {} {}\n'.format(status_code, status_code_message) + \
                    'Date: {}\n'.format(datetime.utcnow())+\
                    'Server: JSON-SERVER v1.0.0\n'+\
                    'Last-Modified: Wed, 22 Jul 2009 19:15:56 GMT\n'+\
                    'Content-Length: {}\n'.format(len(body))+\
                    'Content-Type: application/json\n'+\
                    'Connection: Closed\n\n'+\
                    '{}'.format(body)
    # print (http_response)
    client_socket.send(http_response.encode())
    print ("Done responding user, going to close the socket")
    client_socket.close()
    # TODO: Send log to logger

def http_process(accepted_clients_queue):
    while True:
        try:
            sock, address = accepted_clients_queue.get()
            chunk  = '' # TODO Dont have everything on memory
            breaks_found = 0
            # print (address)
            # while breaks_found < 2:
            chunk += sock.recv(2048).decode()
                # breaks_found += chunk.count('\n\n') # TODO: Malformed requests?
            treat_message(chunk, sock)

        except Exception:
            print (traceback.format_exc())
            send_response_error(500, 'unknown_error', sock)

# def close_sockets():
#     while True:
#         print("Waiting for another socket")
#         socket_to_be_closed = sockets_to_be_closed.get()
#         print("Closing socket")
#         socket_to_be_closed.close()

accepted_clients_queue = Queue()

fileserver_responses_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

fileserver_responses_socket.bind(('127.0.0.1', RESPONSES_PORT))
fileserver_responses_socket.listen(5)


processers = [Process(target=http_process, args=(accepted_clients_queue,)) for i in range(NUMBER_OF_PROCESSERS)]
responders = [Process(target=http_respond, args=(fileserver_responses_socket,)) for i in range(NUMBER_OF_RESPONDERS)]


# sockets_to_be_closed = Queue()

# sockets_closer = Thread(target=close_sockets)
# sockets_closer.start()

for processer in processers:
    processer.start()

for responder in responders:
    responder.start()

incoming_clients_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

incoming_clients_socket.bind(('127.0.0.1', REQUESTS_PORT))
incoming_clients_socket.listen(5)

while True:
    accepted_client = incoming_clients_socket.accept()
    accepted_clients_queue.put(accepted_client)

for processer in processers:
    processer.join()

for responder in responders:
    responder.join()

# sockets_closer.join()
