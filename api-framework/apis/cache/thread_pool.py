import py2neo
from .prefetch_thread import *
from .prefetch_task import AbstractPrefetchTask

class PrefetchPool(object):


    @classmethod
    def from_analyzer(cls, analyzer, thread_count: int = 1):

        return cls(cache_graph=analyzer.cache, connector_profile=analyzer.service_profile, thread_count=thread_count)

    def __init__(self, cache_graph, connector_profile: py2neo.ServiceProfile, thread_count: int = 1):

        self.threads = []
        self.queue = Queue()
        self.cache_graph = cache_graph
        self.thread_count = thread_count
        for i in range(thread_count):
            prefetch_thread = PrefetchThread(queue=self.queue, cache_graph=self.cache_graph,
                                             connector_profile=connector_profile)
            prefetch_thread.daemon = True
            self.threads.append(prefetch_thread)
        self.start_all()
        self.task_count = 0

    def start_all(self):

        for i in self.threads:
            i.start()

    def stop_all(self):

        for i in self.threads:
            i.stop()

    def put_task(self, task):

        assert isinstance(task, AbstractPrefetchTask)
        self.queue.put(task)

    def calculate_count(self):
        for i in self.threads:
            self.task_count += i.task_count

    def get_count(self):
        self.calculate_count()
        return self.task_count