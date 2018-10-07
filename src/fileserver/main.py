import socket
import pickle
import os
import json
from lib.encoder import read_request, encode_response
from configs import FILES_FOLDER, RESPONSES_PORT, FILESERVERS_PORTS, MAINSERVER_NAME, FILESERVER_WORKERS, CACHE_CAPACITY, LOG_FORMAT, LOG_LEVEL
import portalocker
import traceback
import logging
from random import random
import math
from threading import Thread, Condition, Lock
from cache_lru import ProtectedLRUCache
from orchestrator import Orchestrator


logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('fileserver')
logger.setLevel(LOG_LEVEL)


logger.info("Fileserver is up and running :)")


FILES_FOLDER = os.path.join(FILES_FOLDER, str(math.ceil(random() * 100)))
class InternalMethodNotSupported(Exception):
    pass

gracefulQuit = False


orchestrator = Orchestrator()

def treat_request(method, _filename, content, cache):
    filename = _filename[1:] # Remove the first /, so its not saved in the root directory
    logger.info("Going to execute " + method + " to " + os.path.join(FILES_FOLDER, filename))
    
    if method == 'GET':
        response = get(filename, cache)
    elif method == 'PUT':
        response = put(filename, content, cache)
    elif method == 'POST':
        response = post(filename, content, cache)
    elif method == 'DELETE':
        response = delete(filename, cache)
    else:
        raise InternalMethodNotSupported

    logger.info('Finished {} on {}: {}...'.format(method, filename, response[:20]))
    return response
    
def get(filename, cache):
    orchestrator.lock_shared(filename)
    try:
        response = cache.get(filename)
        logger.debug('Hit cache ' + filename)
    except KeyError:    
        logger.debug('Miss cache ' + filename)

        with open(os.path.join(FILES_FOLDER, filename), 'r') as request_file:
            response = request_file.read()
        cache.set(filename, response)
    finally:
        orchestrator.unlock(filename)
    return response, 200

def put(filename, content, cache):
    try:
        orchestrator.lock_exclusive(filename)
        if not os.path.isfile(os.path.join(FILES_FOLDER, filename)):
            raise FileNotFoundError()
        with open(os.path.join(FILES_FOLDER, filename), 'w') as request_file:
            request_file.write(content)
        cache.set(filename, content)
    finally:
        orchestrator.unlock(filename)
    return json.dumps({"status":"ok"}), 200

def post(filename, content, cache):
    orchestrator.lock_exclusive(filename)
    try:
        os.makedirs(os.path.dirname(os.path.join(FILES_FOLDER, filename)), exist_ok=True)
        with open(os.path.join(FILES_FOLDER, filename), 'x') as request_file:
            request_file.write(content)
        cache.set(filename, content)
    finally:
        orchestrator.unlock(filename)
    return json.dumps({"status":"ok", "id": filename}), 201


def delete(filename, cache):
    orchestrator.lock_exclusive(filename)
    try:
        os.remove(os.path.join(FILES_FOLDER, filename))
        cache.remove(filename)
    finally:
        orchestrator.unlock(filename)
    return json.dumps({"status":"ok"}), 200


def fileserver_responder(cache):
    global gracefulQuit
    while not gracefulQuit:
        try:
            c, addr = s.accept()
            request = read_request(lambda x: c.recv(x))
            c.close()
            if request == 'END':
                gracefulQuit = True
            else: 
                client, method, uri_postfix, body = request
                response, status_code = treat_request(method, uri_postfix, body, cache)
            
        except FileExistsError:
            status_code = 500
            logger.warn('File existed')
            response = json.dumps({"status": 'retry_please'}) # This should be done automatically by the accepter, changing the URI and sending it back ideally, but it is very rare to happen anyway ( the probability that one users sends a request and this error happens is one in 10^20 asuming 10^18 files already exist)
        except FileNotFoundError:
            status_code = 404
            logger.warn('File not found')
            response = json.dumps({"status": 'file_not_found'})
        except Exception:
            status_code = 500
            response = json.dumps({"status": 'unknown_error'})
            logger.error(traceback.format_exc())

        try:
            response_encoded = encode_response(client, status_code, response, uri_postfix, method)
            responses_queue_socket = socket.socket()
            responses_queue_socket.connect((MAINSERVER_NAME, RESPONSES_PORT))
            responses_queue_socket.sendall(response_encoded)
            responses_queue_socket.close()
            logger.debug('Sent, closing socket')
        except Exception:
            logger.warn(traceback.format_exc())
            logger.warn('WTF')

if __name__ == "__main__":

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind(('0.0.0.0', FILESERVERS_PORTS))
    s.listen(5)

    cache = ProtectedLRUCache(CACHE_CAPACITY)

    workers = [Thread(target=fileserver_responder, args=(cache,)) for i in range(FILESERVER_WORKERS)]

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()
