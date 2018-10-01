import requests


PREFIX = 'http://localhost:8080'
file1 = {"version": 1}
file2 = {"version": 2}
file3 = {"version": 3}
file4 = {"version": 4}
file5 = {"version": 5}


r = requests.post(PREFIX + '/ok/ok', json=file1)
assert(r.status_code == 200)
id1 = r.json()['id']
r = requests.post(PREFIX + '/ok/ok', json=file2)
assert(r.status_code == 200)
id2 = r.json()['id']
print ("Posts done")

assert(requests.get(PREFIX + '/' + id1).json() == file1 )
assert(requests.get(PREFIX + '/' + id2).json() == file2 )
print ("Gets done")

assert(requests.put(PREFIX + '/' + id1, json=file3).status_code == 200)
assert(requests.put(PREFIX + '/' + id2, json=file4).status_code == 200)
print ("Puts done")

assert(requests.get(PREFIX + '/' + id1).json() == file3 )
assert(requests.get(PREFIX + '/' + id2).json() == file4 )
print ("Gets with update done")

assert(requests.delete(PREFIX + '/' +  id1).status_code == 200)
print ("Delete done")

assert(requests.put(PREFIX + '/' + id1, json=file5).status_code == 404)
assert(requests.get(PREFIX + '/' + id1).status_code == 404)
assert(requests.delete(PREFIX + '/' + id1).status_code == 404)
print ("404 thrown")

assert(requests.get(PREFIX + '/' + id2).json() == file4 )
print ("Get done after deletion")
