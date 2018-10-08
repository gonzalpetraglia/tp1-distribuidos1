from datetime import datetime
import traceback
import logging
import signal
import json
from multiprocessing import Process

from http_responder.http_response import gen_http_response
from configs import STATUS_CODE_MESSAGES, LOG_FORMAT, LOG_LEVEL
from lib.encoder import read_response, decode_client


logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(LOG_LEVEL)

class HttpResponder(Process):
    def __init__(self, incoming_fileserver_responses_socket, logs_queue, clients_in_progress):
        self.incoming_fileserver_responses_socket = incoming_fileserver_responses_socket
        self.logs_queue = logs_queue
        self.clients_in_progress = clients_in_progress
        self.finish = False
        super(HttpResponder, self).__init__()

    def run(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        finish = False
        while not finish:
            self._http_respond()

        self.incoming_fileserver_responses_socket.close()

    def _send_log(self, method, status_code, request_uri, request_datetime, address):
        self.logs_queue.put({
            "method": method,
            "status_code": status_code,
            "request_uri": request_uri,
            "address": address,
            "request_datetime": request_datetime
        })

    def _http_respond(self):
        try:
            fileserver_response_socket, address = self.incoming_fileserver_responses_socket.accept()
            response = read_response(lambda x: fileserver_response_socket.recv(x))
            fileserver_response_socket.close()
            if response == 'END':
                finish = True
            else:
                client_info, status_code, body, request_uri, method = response
                client_socket, address, request_datetime = decode_client(client_info)
                client_socket.settimeout(5)
                logger.info('Going to respond {} {} {}'.format(method, request_uri, status_code))
                logger.debug('Body {}'.format(body))
                status_code_message = STATUS_CODE_MESSAGES[status_code]
                http_response = gen_http_response(status_code, status_code_message, datetime.utcnow(), body)
                client_socket.sendall(http_response.encode())
                logger.info("Done responding user, going to close the socket")
                logger.debug(http_response)
                client_socket.close()
                self._send_log(method, status_code, request_uri, request_datetime, address)
        except Exception:
            logger.error(traceback.format_exc())
            body = json.dumps({"status": "unknown_error"})
            http_response = gen_http_response(500, "Internal Error", datetime.utcnow(), body)
            client_socket.sendall(http_response.encode())
            logger.info("Done responding user, going to close the socket")
            client_socket.close()
        with self.clients_in_progress.get_lock():
            self.clients_in_progress.value -= 1
