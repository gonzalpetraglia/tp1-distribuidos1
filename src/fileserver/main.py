import socket
import os
import json
import traceback
import logging
from random import random
import math
import signal
from threading import Thread

from cache_lru import ProtectedLRUCache
from orchestrator import Orchestrator

from lib.encoder import read_request, encode_response
from lib.response_communicator import communicate_response
from configs import FILES_FOLDER, RESPONSES_PORT, FILESERVERS_PORTS, MAINSERVER_NAME, FILESERVER_WORKERS, CACHE_CAPACITY, LOG_FORMAT, LOG_LEVEL


logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('fileserver')
logger.setLevel(LOG_LEVEL)


logger.info("Fileserver is up and running :)")


FILES_FOLDER = os.path.join(FILES_FOLDER, str(math.ceil(random() * 100)))
gracefulQuit = False


orchestrator = Orchestrator()


class FileServerWorker(Thread):
    def __init__(self, incoming_requests, cache):
        self.incoming_requests = incoming_requests
        self.cache = cache
        self.handlers = {
            'GET': self._get,
            'DELETE': self._delete,
            'POST': self._post,
            'PUT': self._put
        }
        super(FileServerWorker, self).__init__()

    def run(self):

        global gracefulQuit
        while not gracefulQuit:
            self._fileserver_respond()
            
        logger.info('Finished processing')

        
    def _treat_request(self, method, _filename, content):
        filename = _filename[1:] # Remove the first /, so its not saved in the root directory
        logger.info("Going to execute " + method + " to " + os.path.join(FILES_FOLDER, filename))
       
        body, status_code = self.handlers[method](filename, content)

        logger.info('Finished {} on {}: {}...'.format(method, filename, body[:20]))
        return body, status_code
        
    def _get(self, filename, _=None):
        orchestrator.lock_shared(filename)
        try:
            response = self.cache.get(filename)
            logger.debug('Hit cache ' + filename)
        except KeyError:    
            logger.debug('Miss cache ' + filename)

            with open(os.path.join(FILES_FOLDER, filename), 'r') as request_file:
                response = request_file.read()
            self.cache.set(filename, response)
        finally:
            orchestrator.unlock(filename)
        return response, 200

    def _put(self, filename, content):
        try:
            orchestrator.lock_exclusive(filename)
            if not os.path.isfile(os.path.join(FILES_FOLDER, filename)):
                raise FileNotFoundError()
            with open(os.path.join(FILES_FOLDER, filename), 'w') as request_file:
                request_file.write(content)
            self.cache.set(filename, content)
        finally:
            orchestrator.unlock(filename)
        return json.dumps({"status":"ok"}), 200

    def _post(self, filename, content):
        orchestrator.lock_exclusive(filename)
        try:
            os.makedirs(os.path.dirname(os.path.join(FILES_FOLDER, filename)), exist_ok=True)
            with open(os.path.join(FILES_FOLDER, filename), 'x') as request_file:
                request_file.write(content)
            self.cache.set(filename, content)
        finally:
            orchestrator.unlock(filename)
        return json.dumps({"status":"ok", "id": filename}), 201


    def _delete(self, filename, _=None):
        orchestrator.lock_exclusive(filename)
        try:
            os.remove(os.path.join(FILES_FOLDER, filename))
            self.cache.remove(filename)
        finally:
            orchestrator.unlock(filename)
        return json.dumps({"status":"ok"}), 200


    def _fileserver_respond(self):
        global gracefulQuit
        there_is_a_processable_request = False
        try:
            c, addr = self.incoming_requests.accept()
            request = read_request(lambda x: c.recv(x))
            c.close()
            if request == 'END':
                gracefulQuit = True
            else: 
                there_is_a_processable_request = True

                client, method, uri_postfix, body = request
                response, status_code = self._treat_request(method, uri_postfix, body)
            
        except FileExistsError:
            status_code = 500
            logger.warn('File existed')
            response = json.dumps({"status": 'retry_please'}) # This should be done automatically by the accepter, changing the URI and sending it back ideally, but it is very rare to happen anyway ( the probability that one users sends a request and this error happens is one in 10^20 asuming 10^18 files already exist)
        except FileNotFoundError:
            status_code = 404
            logger.warn('File not found')
            response = json.dumps({"status": 'file_not_found'})
        except socket.timeout:
            pass
        except Exception:
            status_code = 500
            response = json.dumps({"status": 'unknown_error'})
            logger.error(traceback.format_exc())
        try:

            if there_is_a_processable_request:
                communicate_response(client, status_code, response, uri_postfix, method, MAINSERVER_NAME, RESPONSES_PORT)
                logger.debug('Sent, closing socket')
        except Exception:
            logger.error(traceback.format_exc())

        
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)


    incoming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    incoming_socket.bind(('0.0.0.0', FILESERVERS_PORTS))
    incoming_socket.listen(5)
    incoming_socket.settimeout(5)

    cache = ProtectedLRUCache(CACHE_CAPACITY)

    workers = [FileServerWorker(incoming_socket, cache) for i in range(20)]

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()
