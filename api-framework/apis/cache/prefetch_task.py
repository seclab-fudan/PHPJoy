import networkx as nx
import py2neo
from typing import List
from abc import ABC, abstractmethod
from apis.const import *
from apis.analysis_framework import AnalysisFramework


class AbstractPrefetchTask(ABC):


    def __init__(self, cache_graph, analysis_framework: AnalysisFramework = None):

        if cache_graph is None:
            raise "Task Wrong!Graph is not definited!!"
        self.cache_graph = cache_graph
        self.analysis_framework = analysis_framework  # type:AnalysisFramework

    @abstractmethod
    def do_task(self):

        return None
