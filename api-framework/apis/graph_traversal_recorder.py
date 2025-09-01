import abc

import py2neo
from typing import Dict, Set, Union, List, Callable
import networkx as nx
from apis.analysis_framework import AnalysisFramework as Neo4jEngine
from apis.const import *
from abc import abstractmethod, ABCMeta


class BaseRecorder(object, metaclass=ABCMeta):

    @abstractmethod
    def __init__(self, neo4j_engine: Neo4jEngine):
        self.neo4j_engine = neo4j_engine
        self.storage_graph = None

    @abstractmethod
    def record(self, node: py2neo.Node, next_node: py2neo.Node) -> bool:
        return True

    @abstractmethod
    def record_origin(self, o: py2neo.Node) -> bool:
        return True


class GraphTraversalRecorder(BaseRecorder):

    def __init__(self, neo4j_engine: Neo4jEngine):
        super(GraphTraversalRecorder, self).__init__(neo4j_engine)
        self.storage_graph = nx.DiGraph()

    def record(self, node: py2neo.Node, next_node: py2neo.Node) -> bool:
        self.storage_graph.add_node(next_node[NODE_INDEX],
                                    **{NODE_LINENO: next_node[NODE_LINENO], NODE_TYPE: next_node[NODE_TYPE]})
        self.storage_graph.add_edge(node[NODE_INDEX], next_node[NODE_INDEX])
        return True

    def record_origin(self, o: py2neo.Node) -> bool:
        self.storage_graph.add_node(o[NODE_INDEX], **{NODE_LINENO: o[NODE_LINENO], NODE_TYPE: o[NODE_TYPE]})
        return True


class GraphTraversalStraightRecorder(BaseRecorder):

    def __init__(self, neo4j_engine: Neo4jEngine):
        super(GraphTraversalStraightRecorder, self).__init__(neo4j_engine)
        self.storage_graph = nx.DiGraph()
        self.loop_structure_instance = {}

    def __switch(self, next_node):
        if next_node in self.loop_structure_instance.keys():
            return self.__switch(self.loop_structure_instance[next_node])
        else:
            return next_node

    def record(self, node: py2neo.Node, next_node: py2neo.Node) -> bool:

        parent_node = self.neo4j_engine.get_ast_parent_node(node)
        if parent_node[NODE_TYPE] == TYPE_FOR and \
                self.neo4j_engine.get_ast_ith_child_node(parent_node, 2) \
                not in self.loop_structure_instance.keys():
            self.loop_structure_instance[
                self.neo4j_engine.get_ast_ith_child_node(parent_node, 2)
            ] = self.neo4j_engine.find_cfg_successors(
                self.neo4j_engine.get_ast_ith_child_node(parent_node, 1)
            )[1]
        elif parent_node[NODE_TYPE] == TYPE_WHILE:
            self.loop_structure_instance[node] = self.neo4j_engine.find_cfg_successors(node)[1]
        elif node[NODE_TYPE] == TYPE_FOREACH:
            self.loop_structure_instance[node] = self.neo4j_engine.find_cfg_successors(node)[1]
        if next_node[NODE_INDEX] < node[NODE_INDEX]:

            if next_node in self.loop_structure_instance.keys():
                next_node = self.__switch(next_node)
            else:
                print("Problem not solved")
                return False

        flow_label = self.neo4j_engine.get_cfg_flow_label(node, next_node)
        self.storage_graph.add_node(next_node[NODE_INDEX],
                                    **{NODE_LINENO: next_node[NODE_LINENO], NODE_TYPE: next_node[NODE_TYPE]})
        self.storage_graph.add_edge(node[NODE_INDEX], next_node[NODE_INDEX], **{CFG_EDGE_FLOW_LABEL: flow_label})
        return True

    def record_origin(self, o: py2neo.Node) -> bool:

        self.storage_graph.add_node(o[NODE_INDEX], **{NODE_LINENO: o[NODE_LINENO], NODE_TYPE: o[NODE_TYPE]})
        return True


class ResultRecorder(BaseRecorder):
    def __init__(self, *args, **kwargs):
        super(ResultRecorder, self).__init__(*args, **kwargs)
        self.storage_graph = nx.DiGraph()

    def record(self, node: py2neo.Node, next_node: py2neo.Node, taint_var: str = "") -> bool:
        self.storage_graph.add_node(next_node[NODE_INDEX],
                                    **{NODE_LINENO: next_node[NODE_LINENO], NODE_TYPE: next_node[NODE_TYPE]})
        self.storage_graph.add_edge(node[NODE_INDEX], next_node[NODE_INDEX], taint_var=taint_var)
        return True

    def record_origin(self, o: py2neo.Node) -> bool:
        self.storage_graph.add_node(o[NODE_INDEX], **{NODE_LINENO: o[NODE_LINENO], NODE_TYPE: o[NODE_TYPE]})
        return True

    def get_all_path(self, origins: List[int], terminals: List[int]):
        paths = []
        for origin in origins:
            for terminal in terminals:
                if self.storage_graph.has_node(origin) and self.storage_graph.has_node(terminal):
                    #  print(str(origin[NODE_INDEX])+" "+str(terminal))
                    for x in nx.all_simple_paths(self.storage_graph, origin, terminal):
                        paths.append(x)
                        break
        return paths

    def get_report(self, origin_ids, terminal_ids, analysis_framework):
        paths = self.get_all_path(origin_ids, terminal_ids)
        file_storage = {}
        report_list = []
        for path in paths:
            path_list = []
            for point in path:
                node = analysis_framework.neo4j_graph.nodes.match(id=point).limit(1).first()
                if file_storage.__contains__(node[NODE_FILEID]):
                    file_name = file_storage.get(node[NODE_FILEID])
                else:
                    file_node = analysis_framework.neo4j_graph.nodes.match(**{NODE_INDEX: node[NODE_FILEID]}).all()
                    if file_node.__len__() == 0:
                        print(node)
                        continue
                    else:
                        file_node = file_node[0]
                    file_name = \
                        analysis_framework.neo4j_graph.relationships.match(nodes=[file_node, None],
                                                                           r_type=FILE_EDGE).all()[
                            0].end_node[NODE_NAME]
                    file_storage[node[NODE_FILEID]] = file_name
                position = {'file_name': file_name, 'lineno': node[NODE_LINENO]}
                path_list.append(position)
            report_list.append(path_list)
        return report_list
