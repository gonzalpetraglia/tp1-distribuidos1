import socket
import time
import os
import logging
import pickle
import signal
import traceback
from multiprocessing import Process, Queue, Value
from ctypes import c_ulong

from configs import NUMBER_OF_RESPONDERS, NUMBER_OF_PROCESSERS, REQUESTS_PORT, RESPONSES_PORT, RESPONSES_SOCKET_LENGTH, REQUESTS_SOCKET_LENGTH, LOG_LEVEL, LOG_FORMAT, FILESERVER_PREFIX, FILESERVER_NAME, NUMBER_OF_FILESERVERS, FILESERVERS_PORTS
from log_module import AuditLogger
from http_processer.http_processer import HttpProcesser
from http_responder.http_responder import HttpResponder
from lib.response_communicator import communicate_end

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(LOG_LEVEL)

logger.info("Mainserver is up and running :)")

class FinishingException(Exception):
    pass

def finish(signum, frame):    
    raise FinishingException

signal.signal(signal.SIGINT, finish)
signal.signal(signal.SIGTERM, finish)

def end_processers(processers_queue, processers):
    for i in range(len(processers)):
        processers_queue.put('END')
    logger.debug('Signaled every processer')
    for processer in processers:
        processer.join()
    logger.debug('Finished all the processers')

def end_fileservers():

    def get_fileserver_address(fileserver_index):
        if FILESERVER_NAME: # Intended for localhost tests
            fileserver_name = FILESERVER_NAME
        else:
            fileserver_name = FILESERVER_PREFIX + str(fileserver_index)
        logger.debug('FILESERVER: {}:{}'.format(fileserver_name, FILESERVERS_PORTS))
        return fileserver_name, FILESERVERS_PORTS
    
    for i in range(NUMBER_OF_FILESERVERS):
        fileserver_name, fileserver_port = get_fileserver_address(i + 1)
        communicate_end(fileserver_name, fileserver_port)
    logger.debug('Finished all the fileservers')

def end_responders(responders):
    def send_message_responders():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', RESPONSES_PORT))
        s.sendall('END'.encode())


    for i in range(len(responders)):
        send_message_responders()
    for responder in responders:
        responder.join()
    logger.debug('Finished all the responders')


def end_logger(logs_queue, logger_process):
    logs_queue.put('END')
    logger_process.join()
    logger.debug('Finished the logger')

if __name__ == "__main__":
    accepted_clients_queue = Queue()
    logs_queue = Queue()
    clients_in_progress = Value(c_ulong, 0, lock=True)

    fileserver_responses_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    fileserver_responses_socket.bind(('0.0.0.0', RESPONSES_PORT))
    fileserver_responses_socket.listen(RESPONSES_SOCKET_LENGTH)


    processers = [HttpProcesser(accepted_clients_queue) for i in range(NUMBER_OF_PROCESSERS)]
    responders = [HttpResponder(fileserver_responses_socket, logs_queue, clients_in_progress) for i in range(NUMBER_OF_RESPONDERS)]
    logger_process = AuditLogger(logs_queue)
    logger.info("Going to start {} processers and {} responders ".format(NUMBER_OF_PROCESSERS, NUMBER_OF_RESPONDERS))

    for processer in processers:
        processer.start()
    for responder in responders:
        responder.start()
    logger_process.start()


    incoming_clients_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    incoming_clients_socket.bind(('0.0.0.0', REQUESTS_PORT))
    incoming_clients_socket.listen(REQUESTS_SOCKET_LENGTH)
    finished = False

    while not finished:
        try:
            logger.debug('Listening for more clients')

            accepted_client = incoming_clients_socket.accept()
            logger.debug('Accepted new client')
            with clients_in_progress.get_lock():
                clients_in_progress.value += 1
            accepted_clients_queue.put(accepted_client)
            
        except FinishingException:
            finished = True
            logger.debug('Going to finish :)')
    incoming_clients_socket.close()
    every_client_finished = False
    while not every_client_finished: 
        every_client_finished = (clients_in_progress.value == 0)
        if not every_client_finished:
            time.sleep(1)

    end_processers(accepted_clients_queue, processers)

    end_fileservers()

    end_responders(responders)

    end_logger(logs_queue, logger_process)

    logger.info('Finished all the work')