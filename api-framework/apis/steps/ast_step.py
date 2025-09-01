from typing import List, Union, Dict, Set
import py2neo
from .abstract_step import AbstractStep
from apis.const import *
from apis.exceptions import Neo4jNodeListIndexError
import logging

logger = logging.getLogger(__name__)


class ASTStep(AbstractStep):

    def __init__(self, parent):

        super().__init__(parent, "ast_step")

    def find_parent_nodes(self, _node: py2neo.Node) -> List[py2neo.Node]:

        self.parent.query_count += 1
        if self.parent._use_cache:
            if self.parent.cache.get_ast_inflow(_node) is None:
                rels = self.parent.neo4j_graph.relationships.match(nodes=[None, _node], r_type=AST_EDGE, ).all()
                self.parent.cache.add_ast_inflow(_node, rels)
                res = [i.start_node for i in rels]
            else:
                self.parent.cache_hit += 1
                res = self.parent.cache.get_ast_inflow(_node)
        # self.parent._threadPool.put_entity(res)
        else:
            res = [i.start_node for i in
                   self.parent.neo4j_graph.relationships.match(nodes=[None, _node], r_type=AST_EDGE, )]
        return list(sorted(res, key=lambda x: x[NODE_INDEX]))

    def find_child_nodes(self, _node: py2neo.Node, include_type: List[str] = None) -> List[py2neo.Node]:

        self.parent.query_count += 1
        if self.parent._use_cache:
            if self.parent.cache.get_ast_outflow(_node) is None:
                rels = self.parent.neo4j_graph.relationships.match(nodes=[_node, None], r_type=AST_EDGE, ).all()
                self.parent.cache.add_ast_outflow(_node, rels)
                res = [i.end_node for i in rels]
            else:
                self.parent.cache_hit +=1
                res = self.parent.cache.get_ast_outflow(_node)
        #   self.parent._threadPool.put_entity(res)
        else:
            ast_rels = self.parent.neo4j_graph.relationships.match(nodes=[_node, None], r_type=AST_EDGE, ).all()
            res = [i.end_node for i in ast_rels]
        res_ = []
        for i in res:
            if include_type is not None:
                if i[NODE_TYPE] in include_type:
                    res_.append(i)
            else:
                res_.append(i)
        return list(sorted(res_, key=lambda x: x[NODE_INDEX]))

    def get_ith_parent_node(self, _node: py2neo.Node, i: int = 0, ignore_error_flag=False) -> py2neo.Node or None:

        _node_cp = self.parent.find_ast_parent_nodes(_node)
        if i <= (_node_cp.__len__() - 1):
            return _node_cp[i]
        else:
            if ignore_error_flag:
                return None
            else:
                raise Neo4jNodeListIndexError(buffer=_node_cp, index=i)

    def get_parent_node(self, _node: py2neo.Node, ignore_error_flag=False) -> Union[py2neo.Node, None]:

        return self.get_ith_parent_node(_node, ignore_error_flag=ignore_error_flag)

    def get_child_node(self, _node: py2neo.Node, ignore_error_flag=False) -> py2neo.Node:

        return self.get_ith_child_node(_node, ignore_error_flag=ignore_error_flag)

    def get_ith_child_node(self, _node: py2neo.Node, i: int = 0, ignore_error_flag=False) -> py2neo.Node or None:

        _node_cp = self.find_child_nodes(_node)
        if i <= (_node_cp.__len__() - 1):
            return _node_cp[i]
        else:
            if ignore_error_flag:
                return None
            else:
                raise Neo4jNodeListIndexError(buffer=_node_cp, index=i)

    def filter_parent_nodes(self, _node: py2neo.Node, max_depth=20, not_include_self: bool = False,
                            node_type_filter: set = FUNCTION_CALL_TYPES | FUNCTION_DECLARE_TYPES) \
            -> Union[py2neo.Node, None]:

        if _node[NODE_TYPE] in node_type_filter:
            return _node
        __node = self.get_parent_node(_node)
        if __node[NODE_TYPE] in node_type_filter:
            return __node
        elif __node[NODE_TYPE] in {TYPE_STMT_LIST}:
            logger.warning("get specify node error ,get EXIT specifier")
            return None
        else:
            return self.filter_parent_nodes(__node, max_depth=max_depth, not_include_self=not_include_self,
                                            node_type_filter=node_type_filter)

    def filter_child_nodes(self, _node: py2neo.Node, max_depth=20, not_include_self: bool = False,
                           node_type_filter: Union[List[str], str, Set[str]] = None) -> List[py2neo.Node]:

        query = f"MATCH (A:AST{{id:{_node[NODE_INDEX]}}})-[:PARENT_OF*{not_include_self.__int__()}..{max_depth}]->(B:AST) "
        if isinstance(node_type_filter, str):
            node_type_filter = [node_type_filter]
        elif isinstance(node_type_filter, Set):
            node_type_filter = [i for i in node_type_filter]
        if node_type_filter is not None:
            query += f" WHERE B.type in {node_type_filter.__str__()}"
        return [b for b, in self.parent.run(
                query + " RETURN B;"
        )]

    def __has_cfg(self, node):
        return self.parent.basic_step.match_relationship({node}, r_type=CFG_EDGE).exists()

    def get_root_node(self, node: py2neo.Node) -> py2neo.Node:

        assert node is not None, logger.warning('[-] Input node must not be none ,recheck your code logic')

        if node[NODE_TYPE] in {TYPE_FUNC_DECL, TYPE_PARAM_LIST, }:
            return node

        parent_node = self.get_parent_node(node)
        if node[NODE_TYPE] in {TYPE_IF}:
            return self.get_child_node(self.get_child_node(node))
        elif node[NODE_TYPE] in {TYPE_IF_ELEM}:
            node = self.get_child_node(node, ignore_error_flag=True)
            if node is None:
                raise NotImplementedError()
            else:
                return node

        elif node[NODE_TYPE] in {TYPE_WHILE}:
            return self.get_child_node(node)
        elif node[NODE_TYPE] in {TYPE_SWITCH_CASE}:
            return self.get_child_node(self.get_parent_node(self.get_parent_node(node)))
        elif parent_node and parent_node in {TYPE_SWITCH_CASE}:
            return self.get_child_node(
                    self.get_parent_node(self.get_parent_node(self.get_parent_node(node))))
        elif parent_node[NODE_TYPE] in {TYPE_IF_ELEM}:
            return self.get_root_node(parent_node)

        while not self.__has_cfg(node) and node is not None:
            _node = self.get_parent_node(node, ignore_error_flag=True)
            if _node is None:
                logger.debug(f"not reachable ; check alg or debug parent node of {node}")
                return None
            node = _node
        return node

    def get_control_node_condition(self, _node: py2neo.Node, ignore_error=False) -> py2neo.Node:

        if not ignore_error:
            assert _node[NODE_TYPE] in {TYPE_IF, TYPE_IF_ELEM, TYPE_WHILE, TYPE_DO_WHILE}
        else:
            if _node[NODE_TYPE] not in {TYPE_IF, TYPE_IF_ELEM, TYPE_WHILE, TYPE_DO_WHILE}:
                return _node
                # , TYPE_FOR, TYPE_FOREACH NOT CONSIDER
        if _node[NODE_TYPE] in {TYPE_WHILE, TYPE_DO_WHILE, TYPE_IF_ELEM}:
            return self.get_ith_child_node(_node, 0)
        if _node[NODE_TYPE] in {TYPE_IF}:
            return self.get_ith_child_node(
                    self.get_ith_child_node(_node, 0), 0
            )

    def find_function_return_expr(self, node: py2neo.Node, ) -> List[py2neo.Node]:
        res = []
        func_exit = self.parent.match_first(LABEL_ARTIFICIAL,
                                            **{NODE_FUNCID: node[NODE_INDEX],
                                               NODE_FILEID: node[NODE_FILEID],
                                               NODE_TYPE: TYPE_CFG_FUNC_EXIT})
        for r in self.parent.match_relationship([None, func_exit], r_type=CFG_EDGE):
            res.append(r.start_node)
        return sorted(res, key=lambda x: x[NODE_INDEX])

    def find_function_entrance_expr(self, node: py2neo.Node, ) -> List[py2neo.Node]:
        res = []
        func_entry = self.parent.match_first(LABEL_ARTIFICIAL,
                                             **{NODE_FUNCID: node[NODE_INDEX],
                                                NODE_FILEID: node[NODE_FILEID],
                                                NODE_TYPE: TYPE_CFG_FUNC_ENTRY})
        for r in self.parent.match_relationship([func_entry, None], r_type=CFG_EDGE):
            res.append(r.end_node)
        return sorted(res, key=lambda x: x[NODE_INDEX])

    def get_function_arg_ith_node(self, node: py2neo.Node, i=0) -> py2neo.Node:

        if node[NODE_TYPE] in {TYPE_EXIT, TYPE_ECHO,
                               TYPE_INCLUDE_OR_EVAL,
                               TYPE_PRINT, TYPE_RETURN,
                               TYPE_UNSET, TYPE_ISSET}:  # 特殊arg
            arg_list = self.find_child_nodes(node)
            return arg_list[i]
        arg_list = self.find_function_arg_node_list(node)
        if arg_list.__len__() == 0:
            logger.fatal(f"warning {node} don't have ARG LIST")
        else:
            try:
                return arg_list[i]
            except IndexError as e:
                logger.warning(f"got {e}  system will return None instead")
                return None

    def find_function_arg_node_list(self, node: py2neo.Node) -> List[py2neo.Node]:

        if node[NODE_TYPE] in {TYPE_INCLUDE_OR_EVAL, TYPE_ECHO, TYPE_PRINT, TYPE_EXIT, TYPE_METHOD, TYPE_RETURN}:
            return self.find_child_nodes(node)

        return self.find_child_nodes(
                self.find_child_nodes(node, include_type=[TYPE_ARG_LIST])[0]
        )

    def get_function_arg_node_cnt(self, node: py2neo.Node) -> int:

        if node[NODE_TYPE] in {TYPE_EXIT, TYPE_ECHO, TYPE_INCLUDE_OR_EVAL, TYPE_PRINT, TYPE_RETURN}:  # 特殊arg
            return 1
        arg_list = self.find_function_arg_node_list(node)
        if arg_list.__len__() == 0:
            logger.fatal(f"warning {node.__str__()} don't have ARG LIST")
            return 0  # return 0 ?
        else:
            try:
                return arg_list.__len__()
            except IndexError as e:
                logger.warning(f"got {e} for {node.__str__()}  system will return None instead")
                return 1

    def get_function_defined_node_by_name(self, name: str, match_matrix: dict = {}):

        if "new " in name:
            name = name.replace("new", "").strip()
            return self.parent.get_class_construct_function(
                    self.parent.get_class_defined_node_by_name(name, **match_matrix)
            )
        return self.parent.neo4j_graph.nodes.match("AST", **match_matrix).where(
                f"_.name='{name}' and _.type in ['AST_METHOD','AST_FUNC_DECL']"
        ).first()

    def get_class_defined_node_by_name(self, name: str, match_matrix: dict = {}):

        return self.parent.neo4j_graph.nodes.match("AST", **match_matrix).where(
                f"_.name='{name}' AND _.type='AST_CLASS'"
        ).first()

    def get_class_construct_function(self, node: py2neo.Node):

        class_top_level_node = self.parent.find_ast_child_nodes(node, include_type=[TYPE_TOPLEVEL])[0]
        class_stmt_list_node = self.parent.find_ast_child_nodes(class_top_level_node, include_type=[TYPE_STMT_LIST])[0]
        for i in self.parent.find_ast_child_nodes(class_stmt_list_node, include_type=[TYPE_METHOD]):
            if i[NODE_NAME] == "__construct":
                return i
        return None
