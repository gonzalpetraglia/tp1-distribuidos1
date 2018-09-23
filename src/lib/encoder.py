import pickle

from multiprocessing.reduction import ForkingPickler
from io import StringIO
import math

MAX_MESSAGE_LENGTH_IN_BYTES = 2 ** (64)


def encode_socket(obj):
    buf = StringIO()
    return bytes(ForkingPickler.dumps(obj))

def decode_response(response_bytes):
    response_dict = pickle.loads(response_bytes)
    return pickle.loads(response_dict['client']), int(response_dict['status_code']), response_dict['body'] 


def encode_request(client_socket, method, URI_postfix, body=None):
    max_bytes_needed_to_encode_length = int(math.log(MAX_MESSAGE_LENGTH_IN_BYTES, 2) / 8)
    # TODO add info about client
    print (body)
    info_to_server = {
        "client": encode_socket(client_socket),
        "method": method,
        "URI_postfix": URI_postfix
    }
    if body:
        info_to_server['body'] = body
    message_to_fileserver = pickle.dumps(info_to_server)
    print(message_to_fileserver)
    return len(message_to_fileserver).to_bytes(max_bytes_needed_to_encode_length, byteorder='big', signed=True) \
            + message_to_fileserver

def encode_response(response_dict):
    response = pickle.dumps(response_dict)
    return len(response).to_bytes(8, byteorder='big', signed=True) +\
                response