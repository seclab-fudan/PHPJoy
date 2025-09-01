from typing import List, Union, Dict, Set
import py2neo
from apis.const import *
from apis.exceptions import Neo4jNodeListIndexError
import networkx as nx
from collections import deque
from apis.helper import StringMatcher
from .abstract_step import AbstractStep


class FIGStep(AbstractStep):
    def __init__(self, parent):
        super().__init__(parent, "fig_step")

    def get_filesystem_node(self, _node: py2neo.Node) -> py2neo.Node:

        return self.parent.basic_step.match_first(LABEL_FILESYSTEM,
                                                  **{NODE_TYPE: "File", NODE_INDEX: _node[NODE_FILEID]})

    def find_include_src(self, _node: py2neo.Node) -> List[py2neo.Node]:

        res = [i.start_node for i in
               self.parent.neo4j_graph.relationships.match(nodes=[None, _node], r_type=INCLUDE_EDGE, )]
        return list(sorted(res, key=lambda x: x[NODE_INDEX]))

    def find_include_dst(self, _node: py2neo.Node) -> List[py2neo.Node]:

        return [i.end_node for i in
                self.parent.neo4j_graph.relationships.match(nodes=[_node, None], r_type=INCLUDE_EDGE, )]

    def get_include_map(self, _node: py2neo.Node) -> nx.DiGraph:

        return_map = nx.DiGraph()
        return_map.add_node(_node.identity, **_node)
        queue: deque[py2neo.Node] = deque()
        queue.append(_node)
        while queue.__len__() != 0:
            current_node = queue.popleft()
            for node in self.parent.find_fig_include_dst(current_node):
                return_map.add_node(node.identity, **_node)
                return_map.add_edge(current_node.identity, node.identity)
                queue.append(node)
        return return_map

    def get_belong_file(self, _node: py2neo.Node) -> str:

        file_system_node = self.parent.match(LABEL_FILESYSTEM, id=_node[NODE_FILEID]).first()
        return self.get_node_from_file_system(file_system_node)[NODE_NAME]

    def get_file_name_node(self, _file_name: str, match_strategy=1) -> Union[py2neo.Node, None]:

        if match_strategy == 1:
            nodes = [i for i in
                     self.parent.match("AST", ).where(
                         f"_.type='{TYPE_TOPLEVEL}' and   _.name CONTAINS '{_file_name}' ")]
            if nodes.__len__() >= 1:
                best_index = StringMatcher.match_best_similar_str_index(_file_name, [i[NODE_NAME] for i in nodes])
                return nodes[best_index]
            else:
                return None  # file not found error;
        elif match_strategy == 0:
            return self.parent.match(LABEL_AST, ).where(f"_.type='{TYPE_TOPLEVEL}' and '{_file_name}' =  _.name").limit(
                1).first()

    def get_node_from_file_system(self, _node: py2neo.Node) -> py2neo.Node:

        r = self.parent.neo4j_graph.relationships.match(nodes=[_node], r_type=FILE_EDGE).first()
        return r.end_node

    def get_toplevel_file_first_statement(self, toplevel_file_node):
        assert toplevel_file_node[NODE_TYPE] in {TYPE_TOPLEVEL} and \
               NODE_FLAGS in toplevel_file_node.keys() and \
               set(toplevel_file_node[NODE_FLAGS]) & {FLAG_TOPLEVEL_FILE}
        stmt = self.parent.get_ast_child_node(toplevel_file_node)
        return self.parent.get_ast_child_node(stmt)

    def get_top_filesystem_node(self, _node: py2neo.Node) -> py2neo.Node:

        return self.parent.match_first(LABEL_FILESYSTEM, **{NODE_TYPE: "File", NODE_INDEX: _node[NODE_FILEID]})
