from lib.encoder import read_response
from datetime import datetime
from configs import STATUS_CODE_MESSAGES, LOG_FORMAT, LOG_LEVEL
import traceback
import logging


logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(LOG_LEVEL)


def send_log(queue, method, status_code, request_uri):
    queue.put({
        "method": method,
        "status_code": status_code,
        "request_uri": request_uri
    })

def http_respond(incoming_fileserver_responses_socket, logs_queue):
    while True:
        try:
            fileserver_response_socket, address = incoming_fileserver_responses_socket.accept()
            client_socket, status_code, body, request_uri, method = read_response(lambda x: fileserver_response_socket.recv(x))
            client_socket.settimeout(5)
            logger.info('Going to respond {} {} {}'.format(method, request_uri, status_code))
            logger.debug('Body {}'.format(body))
            status_code_message = STATUS_CODE_MESSAGES[status_code]
            http_response = 'HTTP/1.1 {} {}\r\n'.format(status_code, status_code_message) + \
                            'Date: {}\r\n'.format(datetime.utcnow())+\
                            'Server: JSON-SERVER v1.0.0\r\n'+\
                            'Content-Length: {}\r\n'.format(len(body)+2)+\
                            'Content-Type: application/json\r\n'+\
                            'Connection: Closed\r\n\r\n'+\
                            '{}\r\n'.format(body)
            client_socket.sendall(http_response.encode())
            logger.info("Done responding user, going to close the socket")
            client_socket.close()
            send_log(logs_queue, method, status_code, request_uri)
        except Exception:
            logger.error(traceback.format_exc())
            http_response = 'HTTP/1.1 {} {}\r\n'.format(500, "Internal Error") + \
                            'Date: {}\r\n'.format(datetime.utcnow())+\
                            'Server: JSON-SERVER v1.0.0\r\n'+\
                            'Content-Length: {}\r\n'.format(len('{"status": "unknown_error"}\r\n'))+\
                            'Content-Type: application/json\r\n'+\
                            'Connection: Closed\r\n\r\n'+\
                            '{"status": "unknown_error"}\r\n'
            client_socket.sendall(http_response.encode())
            logger.info("Done responding user, going to close the socket")
            client_socket.close()
    incoming_fileserver_responses_socket.close()

