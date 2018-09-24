import socket
import pickle
import os
import json
from lib.encoder import encode_response
from config import FILES_FOLDER, RESPONSES_PORT, FILESERVERS_PORTS, MAINSERVER_NAME, FILESERVER_WORKERS, CACHE_CAPACITY
import portalocker
import traceback
import logging
from threading import Thread, Condition, Lock
from cache_lru import ProtectedLRUCache


FORMAT = "%(asctime)-15s %(thread)d %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('fileserver')
logger.setLevel(logging.DEBUG)


logger.info("Fileserver is up and running :)")

class InternalMethodNotSupported(Exception):
    pass

class FolderDoesntExist(Exception):
    pass


class Orchestrator(object):
    is_free_to_go = Condition()
    file_locks = {}
    def lock_exclusive(self, filename):
        with self.is_free_to_go:
            self.is_free_to_go.wait_for(lambda: filename not in self.file_locks)
            self.file_locks[filename] = {"exclusive": True}
    def lock_shared(self, filename):
        with self.is_free_to_go:
            self.is_free_to_go.wait_for(lambda: filename not in self.file_locks or not self.file_locks[filename]["exclusive"])
            threads_with_lock = self.file_locks[filename]["threads_with_lock"] if filename in self.file_locks else 0
            self.file_locks[filename] = {"exclusive": False, "threads_with_lock": threads_with_lock + 1}
    def unlock(self, filename):
        with self.is_free_to_go:
            if self.file_locks[filename]["exclusive"] or self.file_locks[filename]["threads_with_lock"] == 1:
                self.file_locks.pop(filename)
            else:
                self.file_locks[filename]["threads_with_lock"] -= 1
            self.is_free_to_go.notify_all()

orchestrator = Orchestrator()

def treat_request(request_dict, cache):
    method = request_dict['method']
    filename = request_dict['URI_postfix'][1:] # Remove the first /
    logger.info("Going to execute " + method + " to " + os.path.join(FILES_FOLDER, filename))
    if not os.path.isdir(FILES_FOLDER):
        logger.error('File directory doesnt exist')
        raise FolderDoesntExist()
    
    if method == 'GET':
        response = get(filename, cache)
    elif method == 'PUT':
        content = request_dict['body']
        response = put(filename, content, cache)
    elif method == 'POST':
        content = request_dict['body']
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
    
    orchestrator.unlock(filename)
    return response

def put(filename, content, cache):
    orchestrator.lock_exclusive(filename)
    if not os.path.isfile(os.path.join(FILES_FOLDER, filename)):
        raise FileNotFoundError()
    with open(os.path.join(FILES_FOLDER, filename), 'w') as request_file:
        request_file.write(content)
    cache.set(filename, content)
    orchestrator.unlock(filename)
    return json.dumps({"status":"ok"})

def post(filename, content, cache):
    orchestrator.lock_exclusive(filename)
    os.makedirs(os.path.dirname(os.path.join(FILES_FOLDER, filename)), exist_ok=True)
    with open(os.path.join(FILES_FOLDER, filename), 'x') as request_file:
        request_file.write(content)
    cache.set(filename, content)
    orchestrator.unlock(filename)
    return json.dumps({"status":"ok", "id": filename})


def delete(filename, cache):
    orchestrator.lock_exclusive(filename)
    os.remove(os.path.join(FILES_FOLDER, filename))
    cache.remove(filename)
    orchestrator.unlock(filename)
    return json.dumps({"status":"ok"})


def fileserver_responder(cache):
    while True:
        try:
            c, addr = s.accept()
            message_length = int.from_bytes(c.recv(8), byteorder='big', signed=True)
            #print (message_length)
            message = c.recv(message_length)
            # print (message)
            c.close()
            request_dict = pickle.loads(message)
            response = treat_request(request_dict, cache)
            status_code = 200
            
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

        response_dict = {
            "status_code": status_code,
            "body": response,
            "client": request_dict['client'],
            "request_uri": request_dict['URI_postfix'],
            "method": request_dict['method']
        }


        response_encoded = encode_response(response_dict)
        responses_queue_socket = socket.socket()
        responses_queue_socket.connect((MAINSERVER_NAME, RESPONSES_PORT))
        responses_queue_socket.send(response_encoded)
        responses_queue_socket.close()

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
