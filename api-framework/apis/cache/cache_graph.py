import copy
import sys

import networkx as nx
import py2neo
from typing import List
from abc import ABC, abstractmethod
from apis.const import *


class AbstractCacheGraph(ABC):


    def __init__(self, **kwargs):

        self.node_cache_pool = {}
        self.node_source = {}
    @abstractmethod
    def get_node(self, _node_index):

        return self.node_cache_pool.get(_node_index, False)

    @abstractmethod
    def add_node(self, node: py2neo.Node):

        node = copy.deepcopy(node)
        if not node[NODE_INDEX] in self.node_cache_pool.keys():
            self.node_cache_pool[node[NODE_INDEX]] = node


class BasicCacheGraph(AbstractCacheGraph):


    def __init__(self, **kwargs):

        self.ast_cache_graph = nx.DiGraph()
        self.cfg_cache_graph = nx.DiGraph()
        self.pdg_cache_graph = nx.DiGraph()
        self.cg_cache_graph = nx.DiGraph()
        self.node_code_cache_pool = {}
        self.customize_storage = {}
        super().__init__(**kwargs)

    def get_node(self, _node_index):

        return self.node_cache_pool.get(_node_index, False)

    def add_node(self, node: py2neo.Node,source:str='traversal'):

        if not self.ast_cache_graph.has_node(node[NODE_INDEX]):
            self.ast_cache_graph.add_node(node[NODE_INDEX], visiable=0b00)

        if not self.cfg_cache_graph.has_node(node[NODE_INDEX]):
            self.cfg_cache_graph.add_node(node[NODE_INDEX], visiable=0b00)

        if not self.pdg_cache_graph.has_node(node[NODE_INDEX]):
            self.pdg_cache_graph.add_node(node[NODE_INDEX], visiable=0b00)

        if not self.cg_cache_graph.has_node(node[NODE_INDEX]):
            self.cg_cache_graph.add_node(node[NODE_INDEX], visiable=0b00)

        if not self.node_cache_pool.__contains__(node[NODE_INDEX]):
            self.node_cache_pool[node[NODE_INDEX]] = node
            self.node_source[node[NODE_INDEX]] = source

    def add_ast_outflow(self, node: py2neo.Node, relationships: List[py2neo.Relationship]):

        self.add_node(node)
        if not self.ast_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b10:
            self.ast_cache_graph.nodes[node[NODE_INDEX]]['visiable'] |= 0b10
            for relationship in relationships:
                end_node = relationship.end_node
                self.add_node(end_node)
                end_node_id = end_node[NODE_INDEX]
                if not self.ast_cache_graph.has_edge(node[NODE_INDEX], end_node_id):
                    self.ast_cache_graph.add_edge(node[NODE_INDEX], end_node_id)

    def add_ast_inflow(self, node: py2neo.Node, relationships: List[py2neo.Relationship]):

        self.add_node(node)
        if not self.ast_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b01:
            self.ast_cache_graph.nodes[node[NODE_INDEX]]['visiable'] |= 0b01
            for relationship in relationships:
                start_node = relationship.start_node
                self.add_node(start_node)
                start_node_id = start_node[NODE_INDEX]
                if not self.ast_cache_graph.has_edge(start_node_id, node[NODE_INDEX]):
                    self.ast_cache_graph.add_edge(start_node_id, node[NODE_INDEX])

    def get_ast_inflow(self, node: py2neo.Node):

        self.add_node(node)
        if self.ast_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b01:
            rels = [self.node_cache_pool.get(node_id) for node_id in
                    list(self.ast_cache_graph.predecessors(node[NODE_INDEX]))]
            return rels
        return None

    def get_ast_outflow(self, node: py2neo.Node):

        self.add_node(node)
        if self.ast_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b10:
            rels = [self.node_cache_pool.get(node_id) for node_id in
                    list(self.ast_cache_graph.successors(node[NODE_INDEX]))]
            return rels
        return None

    def add_cfg_outflow(self, node: py2neo.Node, relationships: List[py2neo.Relationship]):

        self.add_node(node)
        if not self.cfg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b10:
            self.cfg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] |= 0b10
            for relationship in relationships:
                end_node = relationship.end_node
                self.add_node(end_node)
                end_node_id = end_node[NODE_INDEX]
                if not self.cfg_cache_graph.has_edge(node[NODE_INDEX], end_node_id):
                    self.cfg_cache_graph.add_edge(node[NODE_INDEX], end_node_id)

    def add_cfg_inflow(self, node: py2neo.Node, relationships: List[py2neo.Relationship]):

        self.add_node(node)
        if not self.cfg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b01:
            self.cfg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] |= 0b01
            for relationship in relationships:
                start_node = relationship.start_node
                self.add_node(start_node)
                start_node_id = start_node[NODE_INDEX]
                if not self.cfg_cache_graph.has_edge(start_node_id, node[NODE_INDEX]):
                    self.cfg_cache_graph.add_edge(start_node_id, node[NODE_INDEX])

    def get_cfg_inflow(self, node: py2neo.Node):

        self.add_node(node)
        if self.cfg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b01:
            rels = [self.node_cache_pool.get(node_id) for node_id in
                    list(self.cfg_cache_graph.predecessors(node[NODE_INDEX]))]
            return rels
        return None

    def get_cfg_outflow(self, node: py2neo.Node):

        self.add_node(node)
        if self.cfg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b10:
            rels = [self.node_cache_pool.get(node_id) for node_id in
                    list(self.cfg_cache_graph.successors(node[NODE_INDEX]))]
            return rels
        return None

    def add_pdg_outflow(self, node: py2neo.Node, relationships: List[py2neo.Relationship],source: str='traversal'):

        self.add_node(node,source=source)
        if not self.pdg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b10:
            self.pdg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] |= 0b10
            for relationship in relationships:
                end_node = relationship.end_node
                self.add_node(end_node,source=source)
                end_node_id = end_node[NODE_INDEX]
                if not self.pdg_cache_graph.has_edge(node[NODE_INDEX], end_node_id):
                    self.pdg_cache_graph.add_edge(node[NODE_INDEX], end_node_id,source=source,taint_var = relationship['var'])

    def add_pdg_inflow(self, node: py2neo.Node, relationships: List[py2neo.Relationship], source: str = "traversal"):

        self.add_node(node,source=source)
        if not self.pdg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b01:
            self.pdg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] |= 0b01
            for relationship in relationships:
                start_node = relationship.start_node
                self.add_node(start_node,source=source)
                start_node_id = start_node[NODE_INDEX]
                if not self.pdg_cache_graph.has_edge(start_node_id, node[NODE_INDEX]):
                    self.pdg_cache_graph.add_edge(start_node_id, node[NODE_INDEX], source=source,taint_var = relationship['var'])

    def get_pdg_inflow(self, node: py2neo.Node):

        self.add_node(node)
        if self.pdg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b01:
            rels = [self.node_cache_pool.get(node_id) for node_id in
                    list(self.pdg_cache_graph.predecessors(node[NODE_INDEX]))]
            return rels
        return None

    def get_pdg_outflow(self, node: py2neo.Node):

        self.add_node(node)
        if self.pdg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b10:
            nodes = list(self.pdg_cache_graph.successors(node[NODE_INDEX]))
            res = []
            b = False
            for node_ in nodes:
                taint_var = self.pdg_cache_graph.edges[node[NODE_INDEX],node_]['taint_var']
                source = self.pdg_cache_graph.edges[node[NODE_INDEX], node_]['source']
                _node = self.get_node(node_)
                _node['taint_var'] = taint_var
                if source == 'prefetch':
                    b = True
                res.append(_node)
            return res,b
        return None

    def add_cg_outflow(self, node: py2neo.Node, relationships: List[py2neo.Relationship]):

        self.add_node(node)
        if not self.cg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b10:
            self.cg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] |= 0b10
            for relationship in relationships:
                end_node = relationship.end_node
                self.add_node(end_node)
                end_node_id = end_node[NODE_INDEX]
                if not self.cg_cache_graph.has_edge(node[NODE_INDEX], end_node_id):
                    self.cg_cache_graph.add_edge(node[NODE_INDEX], end_node_id)

    def add_cg_inflow(self, node: py2neo.Node, relationships: List[py2neo.Relationship]):

        self.add_node(node)
        if not self.cg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b01:
            self.cg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] |= 0b01
            for relationship in relationships:
                start_node = relationship.start_node
                self.add_node(start_node)
                start_node_id = start_node[NODE_INDEX]
                if not self.cg_cache_graph.has_edge(start_node_id, node[NODE_INDEX]):
                    self.cg_cache_graph.add_edge(start_node_id, node[NODE_INDEX])

    def get_cg_inflow(self, node: py2neo.Node):

        self.add_node(node)
        if self.cg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b01:
            rels = [self.node_cache_pool.get(node_id) for node_id in
                    list(self.cg_cache_graph.predecessors(node[NODE_INDEX]))]
            return rels
        return None

    def get_cg_outflow(self, node: py2neo.Node):

        self.add_node(node)
        if self.cg_cache_graph.nodes[node[NODE_INDEX]]['visiable'] & 0b10:
            rels = [self.node_cache_pool.get(node_id) for node_id in
                    list(self.cg_cache_graph.successors(node[NODE_INDEX]))]
            return rels
        return None

    def add_node_code_cache(self, node: py2neo.Node, code: str):

        if not self.node_code_cache_pool.__contains__(node[NODE_INDEX]):
            self.node_code_cache_pool[node[NODE_INDEX]] = code

    def get_node_code(self, node: py2neo.Node):

        return self.node_code_cache_pool.get(node[NODE_INDEX], None)

