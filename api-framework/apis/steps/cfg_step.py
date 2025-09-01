from typing import List, Union, Dict, Set
import py2neo
from apis.const import *
from .abstract_step import AbstractStep


class CFGStep(AbstractStep):
    def __init__(self, parent):
        super().__init__(parent, "cfg_step")

    def find_predecessors(self, _node: py2neo.Node) -> List[py2neo.Node]:

        if self.parent._use_cache:
            if self.parent.cache.get_cfg_inflow(_node) is None:
                rels = self.parent.neo4j_graph.relationships.match(nodes=[None, _node], r_type=CFG_EDGE, ).all()
                self.parent.cache.add_cfg_inflow(_node, rels)
                res = [i.start_node for i in rels]
            else:
                res = self.parent.cache.get_cfg_inflow(_node)
        else:
            res = [i.start_node for i in
                   self.parent.neo4j_graph.relationships.match(nodes=[None, _node], r_type=CFG_EDGE, )]
        return list(sorted(res, key=lambda x: x[NODE_INDEX]))

    def find_successors(self, _node: py2neo.Node) -> List[py2neo.Node]:

        if self.parent._use_cache:
            if self.parent.cache.get_cfg_outflow(_node) is None:
                rels = self.parent.neo4j_graph.relationships.match(nodes=[_node, None], r_type=CFG_EDGE, ).all()
                self.parent.cache.add_cfg_outflow(_node, rels)
                res = [i.end_node for i in rels]
            else:
                res = self.parent.cache.get_cfg_outflow(_node)
        else:
            res = [i.end_node for i in
                   self.parent.neo4j_graph.relationships.match(nodes=[_node, None], r_type=CFG_EDGE, )]
        return list(sorted(res, key=lambda x: x[NODE_INDEX]))

    def get_flow_label(self, _node_start: py2neo.Node, _node_end: py2neo.Node) -> List[str]:

        return [i.get(CFG_EDGE_FLOW_LABEL) for i in
                self.parent.neo4j_graph.relationships.match(nodes=[_node_start, _node_end], r_type=CALLS_EDGE, )]

    def has_cfg(self, start_node, end_node=None):
        if end_node is None:
            return self.parent.basic_step.match_relationship({start_node}, r_type=CFG_EDGE).exists()
        else:
            return self.parent.basic_step.match_relationship([start_node, end_node], r_type=CFG_EDGE).exists()
