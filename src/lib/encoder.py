import pickle

from multiprocessing.reduction import ForkingPickler
from io import StringIO
import math

MAX_MESSAGE_LENGTH_IN_BYTES = 2 ** (32)
MAX_BYTES_NEEDED_FOR_LENGTH = math.ceil(math.log(MAX_MESSAGE_LENGTH_IN_BYTES, 2) / 8)

def _encode_socket(obj):
    buf = StringIO()
    return bytes(ForkingPickler.dumps(obj))

def encode_client(socket, request_time, address):
    client_info = {
        "socket": _encode_socket(socket),
        "address": address,
        "request_time": request_time
    }
    return pickle.dumps(client_info)

def decode_client(encoded_client):
    client_info = pickle.loads(encoded_client)
    return pickle.loads(client_info["socket"]), client_info['address'], client_info['request_time']

def encode_request(client_info, method, URI_postfix, body=None):
    info_to_server = {
        "client": client_info,
        "method": method,
        "URI_postfix": URI_postfix
    }
    if body:
        info_to_server['body'] = body
    message_to_fileserver = pickle.dumps(info_to_server)
    return len(message_to_fileserver).to_bytes(MAX_BYTES_NEEDED_FOR_LENGTH, byteorder='big', signed=False) \
            + message_to_fileserver

def read_request(read):
    response_length_encoded = b''
    while len(response_length_encoded) < MAX_BYTES_NEEDED_FOR_LENGTH:
        bytes_to_be_read = MAX_BYTES_NEEDED_FOR_LENGTH - len(response_length_encoded)
        response_length_encoded += read(bytes_to_be_read)
    message_length = int.from_bytes(response_length_encoded, byteorder='big', signed=False)
    message = b''
    while len(message) < message_length:
        message = read(message_length - len(message))
    request_dict = pickle.loads(message)
    body = request_dict['body'] if 'body' in request_dict else None
    return request_dict['client'], request_dict['method'], request_dict['URI_postfix'], body


def encode_response(client, status_code, body, request_uri, method):
    response_dict = {
        "client": client,
        "status_code": status_code,
        "method": method,
        "body": body,
        "request_uri": request_uri
    }
    response = pickle.dumps(response_dict)
    return len(response).to_bytes(MAX_BYTES_NEEDED_FOR_LENGTH, byteorder='big', signed=False) +\
                response


def read_response(read):
    response_length_encoded = b''
    while len(response_length_encoded) < MAX_BYTES_NEEDED_FOR_LENGTH:
        bytes_to_be_read = MAX_BYTES_NEEDED_FOR_LENGTH - len(response_length_encoded)
        response_length_encoded += read(bytes_to_be_read)
    response_length = int.from_bytes(response_length_encoded, byteorder='big', signed=False)
    response_bytes = b''
    while len(response_bytes) < response_length:
        response_bytes = read(response_length - len(response_bytes))
    response_dict = pickle.loads(response_bytes)
    return response_dict['client'], int(response_dict['status_code']), response_dict['body'], response_dict['request_uri'], response_dict['method']

