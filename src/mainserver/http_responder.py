from lib.encoder import decode_response
from datetime import datetime
from config import STATUS_CODE_MESSAGES, logger
import traceback

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
            response_length_encoded = fileserver_response_socket.recv(4)
            response_length = int.from_bytes(response_length_encoded, byteorder='big', signed=True)

            response = fileserver_response_socket.recv(response_length)
            client_socket, status_code, body, request_uri, method = decode_response(response)
            logger.info('Going to respond {} {} {}'.format(method, request_uri, status_code))
            logger.debug('Body {}'.format(body))
            status_code_message = STATUS_CODE_MESSAGES[status_code]
            http_response = 'HTTP/1.1 {} {}\r\n'.format(status_code, status_code_message) + \
                            'Date: {}\r\n'.format(datetime.utcnow())+\
                            'Server: JSON-SERVER v1.0.0\r\n'+\
                            'Last-Modified: Wed, 22 Jul 2009 19:15:56 GMT\r\n'+\
                            'Content-Length: {}\r\n'.format(len(body)+2)+\
                            'Content-Type: application/json\r\n'+\
                            'Connection: Closed\r\n\r\n'+\
                            '{}\r\n\r\n'.format(body)
            client_socket.sendall(http_response.encode())
            logger.info("Done responding user, going to close the socket")
            client_socket.close()
            send_log(logs_queue, method, status_code, request_uri)
        except Exception:
            logger.error(traceback.format_exc())
            http_response = 'HTTP/1.1 {} {}\r\n'.format(500, "Internal Error") + \
                            'Date: {}\r\n'.format(datetime.utcnow())+\
                            'Server: JSON-SERVER v1.0.0\r\n'+\
                            'Last-Modified: Wed, 22 Jul 2009 19:15:56 GMT\r\n'+\
                            'Content-Length: {}\r\n'.format(len('{"status": "unknown_error"}'))+\
                            'Content-Type: application/json\r\n'+\
                            'Connection: Closed\r\n\r\n'+\
                            '{"status": "unknown_error"}\r\n\r\n'
            client_socket.sendall(http_response.encode())
            logger.info("Done responding user, going to close the socket")
            client_socket.close()
    incoming_fileserver_responses_socket.close()

