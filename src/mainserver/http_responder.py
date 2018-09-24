from lib.encoder import decode_response
import logging
from datetime import datetime
from config import STATUS_CODE_MESSAGES
import traceback


FORMAT = "%(asctime)-15s %(process)d %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(logging.DEBUG)

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

