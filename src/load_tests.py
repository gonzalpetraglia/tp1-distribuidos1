import socket
from multiprocessing import Process, Pool
import requests
import time

from large_file import very_large_file

NUMBER_OF_REQUESTS_PER_PROCESS  = 10
NUMBER_OF_PROCESSES = 10
PREFIX = 'http://localhost:8080'
def post_get(params):
    prefix, process, N = params
    for i in range(N):
        try:
            body = {"jojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojov": "jojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovvvvvjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovvjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojovjojojojojojovvvvvvvvvvvvvvvvvvvvvvvjojojojojojojojojojojojojojojojojojov"}
            resp = requests.post(prefix + '/ok/ok', json=body)
            assert(resp.status_code == 200)
            resp = requests.get(prefix + '/' + resp.json()['id'])
            assert(resp.json() == body)
        except Exception as e:
            print(resp.text)
            print(e)
            raise e
        if i % 100 == 0:
            print ("Iteration {} of process {} done".format(i, process ))

p = Pool(NUMBER_OF_PROCESSES)
p.map(post_get, [[PREFIX, i, NUMBER_OF_REQUESTS_PER_PROCESS] for i in range(NUMBER_OF_PROCESSES)])



def put_parallel():

    def replace_file(process_number, _id ):
        data = ''
        for i in range(3000):
            data += str(process_number)  + (',' if i != 3000 -1 else '') 
        r = requests.put(PREFIX + '/' + _id, json={"data": data})
        assert (r.status_code == 200)

    def is_valid_file(file_data):
        numbers = file_data.split(',')
        if len(numbers) != 3000:
            return False
        initial_number = numbers[0]
        for number in numbers:
            if number != initial_number:
                return False
        print("Everything is ok, process that made it {} ".format(number))
        return True

    _id = requests.post(PREFIX + '/ok/ok', json={"replaceable": True}).json()['id']

    processes = [Process(target=replace_file, args=(i,_id)) for i in range(100)]

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    final_file = requests.get(PREFIX + '/' + _id).json()
    assert(is_valid_file(final_file['data']))


put_parallel()


def post_get_large_file():
    _id = requests.post(PREFIX + '/ok/ok', json=very_large_file).json()['id']
    response_file = requests.get(PREFIX + '/' + _id).json()
    assert(response_file == very_large_file)
    print("Large file well handled")

post_get_large_file()