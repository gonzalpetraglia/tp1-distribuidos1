import socket
from multiprocessing import Process, Pool
import requests
import time

NUMBER_OF_REQUESTS_PER_PROCESS  = 1000
NUMBER_OF_PROCESSES = 100

def post_get(params):
    prefix, process, N = params
    for i in range(N):
        try:
            resp = requests.post(prefix + '/ok/ok', json=({"jojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojov": "jojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovvvvvjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovvjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojov"}))
            resp = requests.get(prefix + '/' + resp.json()['id'])
            resp.json()
        except Exception as e:
            print(resp.text)
            print(e)
            raise e
        if i % 100 == 0:
            print ("Iteration {} of process {} done".format(i, process ))

tic = time.clock()
p = Pool(NUMBER_OF_PROCESSES)
print(p.map(post_get, [['http://localhost:8080', i, NUMBER_OF_REQUESTS_PER_PROCESS] for i in range(NUMBER_OF_PROCESSES)]))
toc = time.clock()
print (toc - tic)
