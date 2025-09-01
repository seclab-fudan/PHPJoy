from typing import List, Union, Dict, Set
import py2neo
from apis.const import *
from apis.exceptions import Neo4jNodeListIndexError
import networkx
from .abstract_step import AbstractStep


class PDGStep(AbstractStep):
    def __init__(self, parent):
        super().__init__(parent, "pdg_step")

    def find_use_nodes(self, _node: py2neo.Node) -> List[py2neo.Node]:

        self.parent.query_count += 1
        if self.parent._use_cache:
            if self.parent.cache.get_pdg_outflow(_node) is None:
                res = []
                rels = self.parent.neo4j_graph.relationships.match(nodes=[_node, None], r_type=DATA_FLOW_EDGE, ).all()
                self.parent.cache.add_pdg_outflow(_node, rels)
                for rel in rels:
                    n = rel.end_node
                    n['taint_var'] = rel['var']
                    res.append(n)
            else:
                self.parent.cache_hit += 1
                res,b = self.parent.cache.get_pdg_outflow(_node)
                if b:
                    self.parent.prefetch_hit += 1
        else:
            res = []
            rels = self.parent.neo4j_graph.relationships.match(nodes=[_node, None], r_type=DATA_FLOW_EDGE, ).all()
            for rel in rels:
                n = rel.end_node
                n['taint_var'] = rel['var']
                res.append(n)

        return list(sorted([i for i in res if i is not None], key=lambda x: x[NODE_INDEX]))

    def find_def_nodes(self, _node: py2neo.Node) -> List[py2neo.Node]:

        if self.parent._use_cache:
            if self.parent.cache.get_pdg_inflow(_node) is None:
                rels = self.parent.neo4j_graph.relationships.match(nodes=[None, _node], r_type=DATA_FLOW_EDGE, ).all()
                self.parent.cache.add_pdg_inflow(_node, rels)
                res = [i.start_node for i in rels]
            else:
                res = self.parent.cache.get_pdg_inflow(_node)

        else:
            res = [i.start_node for i in
                   self.parent.neo4j_graph.relationships.match(nodes=[None, _node], r_type=DATA_FLOW_EDGE, )]

        return list(sorted(res, key=lambda x: x[NODE_INDEX]))

    def get_related_vars(self, _node_start: py2neo.Node, _node_end: py2neo.Node) -> List[str]:

        return [i.get(DATA_FLOW_SYMBOL) for i in
                self.parent.neo4j_graph.relationships.match(nodes=[_node_start, _node_end], r_type=CALLS_EDGE, )]
