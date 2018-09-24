from threading import Condition

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