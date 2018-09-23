import socket
import pickle
import os
import json
from lib.encoder import encode_response
from config import FILES_FOLDER
import portalocker
import traceback
RESPONSES_PORT = int(os.environ.get('RESPONSES_PORT', 8090))


class InternalMethodNotSupported(Exception):
    pass

class FolderDoesntExist(Exception):
    pass

def treat_request(request_dict):
    method = request_dict['method']
    filename = request_dict['URI_postfix'][1:] # Remove the first /
    print ("Going to execute " + method + " to " + os.path.join(FILES_FOLDER, filename) )
    if not os.path.isdir(FILES_FOLDER):
        print ('File directory doesnt exist')
        raise FolderDoesntExist()
    
    if method == 'GET':
        return get(filename)
    elif method == 'PUT':
        content = request_dict['body']
        put(filename, content)
    elif method == 'POST':
        content = request_dict['body']
        post(filename, content)
    elif method == 'DELETE':
        delete(filename)
    else:
        raise InternalMethodNotSupported


# TODO this assumes, there is only one process doing this
def get(filename):
    with portalocker.Lock(os.path.join(FILES_FOLDER, filename), mode='r', flags=portalocker.LOCK_SH) as request_file:
        return request_file.read()

def put(filename, content):
    with portalocker.Lock(os.path.join(FILES_FOLDER, filename), mode='w', flags=portalocker.LOCK_EX) as request_file:
        request_file.write(content)

def post(filename, content):
    os.makedirs(os.path.dirname(os.path.join(FILES_FOLDER, filename)), exist_ok=True)
    print(os.path.isdir(os.path.dirname(os.path.join(FILES_FOLDER, filename))))
    with portalocker.Lock(os.path.join(FILES_FOLDER, filename), mode='x', flags=portalocker.LOCK_EX) as request_file:
        request_file.write(content)

def delete(filename):
    with portalocker.Lock(os.path.join(FILES_FOLDER, filename), mode='r', flags=portalocker.LOCK_EX) as request_file:
        os.remove(os.path.join(FILES_FOLDER, filename))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('127.0.0.1', 9000))
s.listen(5)

while True:
    try:
        c, addr = s.accept()
        message_length = int.from_bytes(c.recv(8), byteorder='big', signed=True)
        #print (message_length)
        message = c.recv(message_length)
        # print (message)
        c.close()
        request_dict = pickle.loads(message)
        response = treat_request(request_dict)
        status_code = 200
        
    except FileExistsError:
        status_code = 500
        response = json.dumps({"status": 'retry_please'}) # This should be done automatically by the accepter, changing the URI and sending it back ideally, but it is very rare to happen anyway ( the probability that one users sends a request and this error happens is one in 10^20 asuming 10^18 files already exist)
    except FileNotFoundError:
        status_code = 404
        response = json.dumps({"status": 'file_not_found'})
    except Exception:
        status_code = 500
        response = json.dumps({"status": 'unknown_error'})
        print (traceback.format_exc())

    response = str(response) if response is not None else json.dumps({"status":"ok"})
    response_dict = {
        "status_code": status_code,
        "body": response,
        "client": request_dict['client'],
        "request_uri": request_dict['URI_postfix']
    }

    response_encoded = encode_response(response_dict)
    responses_queue_socket = socket.socket()
    responses_queue_socket.connect(('127.0.0.1', RESPONSES_PORT))
    responses_queue_socket.send(response_encoded)
    responses_queue_socket.close()
