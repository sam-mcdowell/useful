from multiprocessing import Process, Queue

class DoStuff(object):
    """
    A convenience wrapper for parallelizing work
    """
    def __init__(self):
        self.q = Queue()
        self.processes = set()

    def _queue_thing(self, func):
        return lambda *args, **kwargs: self.q.put(func(*args, **kwargs))

    def do_thing(self, func, args=[], kwargs={}):
        queued_func = self._queue_thing(func)
        p = Process(target=queued_func, args=args, kwargs=kwargs)
        p.start()
        self.processes.add(p)

    def drain_things(self):
        for p in self.processes:
            p.join()
        while not self.q.empty():
            yield self.q.get()
        self.processes.clear()
