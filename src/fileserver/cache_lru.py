import collections
from threading import Lock

class ProtectedLRUCache:
    
    def __init__(self, capacity):
        self.capacity = capacity # Note that this capacity is in # of keys, value pairs; maybe this should be changed to a memory usage capacity
        self.cache = collections.OrderedDict()
        self.lock = Lock()

    def get(self, key):
        with self.lock:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value

    def set(self, key, value):
        with self.lock:
            if self.capacity:
                try:
                    self.cache.pop(key)
                except KeyError:
                    if len(self.cache) >= self.capacity:
                        self.cache.popitem(last=False)
                self.cache[key] = value

    def remove(self, key):
        with self.lock:
            try:
                self.cache.pop(key)
            except KeyError:
                pass