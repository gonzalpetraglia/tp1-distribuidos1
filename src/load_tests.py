import socket
from multiprocessing import Process
import requests

def connect():
    r = requests.get('http://127.0.0.1:8080')
    print r.status_code, r.text

processes = [Process(target=connect) for i in range(20)]

for process in processes:
    process.start()
    
for process in processes:
    process.join()

