import socket
from multiprocessing import Process, Pool
import requests
import time


def post_get(prefix):
    resp = requests.post(prefix + '/gar/ompa', json=({"jojo": "jo"})).json()
    print (resp)
    resp = requests.get(prefix + '/' + resp['id']).json()
    print (resp)

tic = time.clock()
p = Pool(10)
print(p.map(post_get, ['http://localhost:8080' for i in range(100)]))
toc = time.clock()
print (toc - tic)