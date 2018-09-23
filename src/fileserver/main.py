import socket
import pickle
import os
from lib.encoder import encode_response
from config import FILES_FOLDER
RESPONSES_PORT = int(os.environ.get('RESPONSES_PORT', 8090))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('127.0.0.1', 9000))
s.listen(5)



while True:
    c, addr = s.accept()
    message_length = int.from_bytes(c.recv(8), byteorder='big', signed=True)
    #print (message_length)
    message = c.recv(message_length)
    # print (message)
    c.close()
    request_dict = pickle.loads(message)
    response_dict = {
        "status_code": 200,
        "body": '{"hello": "Hrd"}',
        "client": request_dict['client']
    }
    response_encoded = encode_response(response_dict)
    responses_queue_socket = socket.socket()
    responses_queue_socket.connect(('127.0.0.1', RESPONSES_PORT))
    responses_queue_socket.send(response_encoded)
    responses_queue_socket.close()
