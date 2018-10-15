import collections
from threading import Lock
from multiprocessing import Manager

class ProtectedLRUCache:
    def __init__(self, capacity):
        m = Manager()
        self.capacity = capacity
        self.tm = m.Value('i', 0)
        self.cache = m.dict()
        self.lru = m.dict()
        self.lock = m.Lock()


    def get(self, key):
        with self.lock:
            self.lru[key] = self.tm.value
            self.tm.value += 1
            return self.cache[key]

    def set(self, key, value):
        with self.lock:
            if self.capacity:
                if len(self.cache) >= self.capacity:
                    # find the LRU entry
                    old_key = min(self.lru.keys(), key=lambda k:self.lru[k])
                    self.cache.pop(old_key)
                    self.lru.pop(old_key)
                self.cache[key] = value
                self.lru[key] = self.tm.value
                self.tm.value += 1

    def remove(self, key):
        with self.lock:
            try:
                self.cache.pop(key)
            except KeyError:
                pass
