import queue
import threading
from queue import Queue
from apis.cache.cache_graph import *
from apis.analysis_framework import AnalysisFramework
import py2neo


class PrefetchThread(threading.Thread):


    def __init__(self, queue: Queue, cache_graph, connector_profile: py2neo.ServiceProfile):

        super(PrefetchThread, self).__init__()
        self.analysis_framework = AnalysisFramework.from_dict({
                "NEO4J_HOST": connector_profile.host,
                "NEO4J_USERNAME": connector_profile.user,
                "NEO4J_PASSWORD": connector_profile.password,
                "NEO4J_PORT": connector_profile.port,
                "NEO4J_PROTOCOL": connector_profile.protocol,
                "NEO4J_DATABASE": "neo4j",
        }, cache_graph=cache_graph)
        self.queue = queue
        self.task_count = 0
        self.running = False

    def run(self):

        self.running = True
        while self.running:
            task = self.queue.get()
            task.analysis_framework = self.analysis_framework
            b = task.do_task()
            if b:
                self.task_count += 1

    def stop(self):

        self.running = False
