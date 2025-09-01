from typing import List, Union, Dict, Set
import py2neo
from apis.const import *
from apis.exceptions import Neo4jQuickCodeGenerationError
from .abstract_step import AbstractStep
import logging

logger = logging.getLogger(__name__)


def _normalize(x):

    if x is None:
        return None
    return x.strip('\'').strip('\"')


class CodeStep(AbstractStep):
    def __init__(self, parent):
        super(CodeStep, self).__init__(parent,"code_step")
        self._register_lambda_functions()
        self._class_method = {i for i in self.__dir__() if not i.__str__().startswith("_")}

    def _register_lambda_functions(self):

        self.get_string_code = lambda x: _normalize(x[NODE_CODE]) \
            if self._node_type_assertion(x, TYPE_STRING) else None
        self.get_integer_code = lambda x: x[NODE_CODE].__str__() \
            if self._node_type_assertion(x, TYPE_INTEGER) else None
        self.get_double_code = lambda x: x[NODE_CODE].__str__() \
            if self._node_type_assertion(x, TYPE_DOUBLE) else None
        self.get_bool_code = lambda x: x[NODE_CODE].__str__() \
            if self._node_type_assertion(x, TYPE_BOOL) else None
        self.get_ast_method_code = lambda x: x[NODE_NAME].__str__() \
            if self._node_type_assertion(x, TYPE_METHOD) else None
        self.get_ast_function_decl_code = lambda x: x[NODE_NAME].__str__() \
            if self._node_type_assertion(x, TYPE_FUNC_DECL) else None

    def get_node_code(self, node: py2neo.Node, ) -> str:


        code = None
        if node[NODE_TYPE] == TYPE_EXIT:
            code = "die"
        elif node[NODE_TYPE] == TYPE_FUNC_DECL:
            code = self.parent.ast_step.get_ith_child_node(node,0)[NODE_CODE]
        elif node[NODE_TYPE] == TYPE_ISSET:
            code = "isset"
        elif node[NODE_TYPE] == TYPE_ECHO:
            code = "echo"
        elif node[NODE_TYPE] == TYPE_PRINT:
            code = "print"
        elif node[NODE_TYPE] == TYPE_RETURN:
            code = "return"
        elif node[NODE_TYPE] == TYPE_UNSET:
            code = "unset"
        elif node[NODE_TYPE] == TYPE_EMPTY:
            code = "empty"
        elif node[NODE_TYPE] == TYPE_INCLUDE_OR_EVAL and (
                set(node[NODE_FLAGS]) & {FLAG_EXEC_INCLUDE, FLAG_EXEC_INCLUDE_ONCE, FLAG_EXEC_REQUIRE,
                                         FLAG_EXEC_REQUIRE_ONCE}):
            if set(node[NODE_FLAGS]) & {FLAG_EXEC_INCLUDE}:
                code = "include"
            if set(node[NODE_FLAGS]) & {FLAG_EXEC_INCLUDE_ONCE}:
                code = "include_once"
            if set(node[NODE_FLAGS]) & {FLAG_EXEC_REQUIRE}:
                code = "require"
            if set(node[NODE_FLAGS]) & {FLAG_EXEC_REQUIRE_ONCE}:
                code = "require_once"
        elif node[NODE_TYPE] == TYPE_BREAK:
            code = "break"
        elif node[NODE_TYPE] == TYPE_INCLUDE_OR_EVAL and (set(node[NODE_FLAGS]) & {FLAG_EXEC_EVAL}):
            code = "eval"
        elif node[NODE_TYPE] == TYPE_NULL:
            code = 'null'

        if code is not None:
            return code

        if "get_{}_code".format(node[NODE_TYPE].lower()) not in self._class_method:
            if node[NODE_TYPE] not in {
                TYPE_ASSIGN, TYPE_POST_INC, TYPE_ASSIGN_REF, TYPE_PRE_INC,
                TYPE_ASSIGN_OP, TYPE_UNARY_OP, TYPE_BINARY_OP
            }:
                logger.warning(f"call no reg function with node type {node[NODE_TYPE]}")
            code = f"NOT_SUPPORT_FOR_{node[NODE_TYPE]}"
        else:
            code = eval("self.get_{}_code(node)".format(node[NODE_TYPE].lower()))
        return code

    def get_ast_new_code(self, node: py2neo.Node) -> str:
        assert node[NODE_TYPE] == TYPE_NEW
        if self.parent.get_ast_child_node(self.parent.get_ast_child_node(node))[NODE_CODE] is not None:
            return self.parent.get_ast_child_node(self.parent.get_ast_child_node(node))[NODE_CODE]
        elif self.parent.get_ast_child_node(node)[NODE_TYPE] == TYPE_PROP:
            return self.parent.get_ast_prop_code(self.parent.get_ast_child_node(node))
        else:
            raise Neo4jQuickCodeGenerationError(TYPE_NEW + node.__str__())

    def get_ast_var_code(self, node: py2neo.Node) -> str:
        assert node[NODE_TYPE] == TYPE_VAR

        if NODE_CODE in self.parent.get_ast_child_node(node).keys():
            return '$' + self.parent.get_ast_child_node(node)[NODE_CODE]
        elif NODE_CODE in self.parent.get_ast_child_node(self.parent.get_ast_child_node(node)).keys():

            return '$$' + self.parent.get_ast_child_node(self.parent.get_ast_child_node(node))[NODE_CODE]
        else:
            return '$uk'

    def _node_type_assertion(self, node: py2neo.Node, TYPE):
        assert node[NODE_TYPE] == TYPE
        return True

    def get_ast_const_code(self, node: py2neo.Node) -> str:

        assert node[NODE_TYPE] == TYPE_CONST
        return self.parent.get_ast_child_node(self.parent.get_ast_child_node(node))[NODE_CODE]

    def get_ast_prop_code(self, node: py2neo.Node) -> str:

        assert node[NODE_TYPE] == TYPE_PROP
        attribute = _normalize(self.parent.get_ast_ith_child_node(node, -1)[NODE_CODE])
        clazz = self.parent.get_ast_child_node(self.parent.get_ast_ith_child_node(node, 0))[NODE_CODE]
        return f"${clazz}->{attribute}"

    def get_ast_static_prop_code(self, node: py2neo.Node) -> str:

        assert node[NODE_TYPE] == TYPE_STATIC_PROP
        attribute = _normalize(self.parent.get_ast_ith_child_node(node, -1)[NODE_CODE])
        clazz = self.parent.get_ast_child_node(self.parent.get_ast_ith_child_node(node, 0))[NODE_CODE]
        return f"{clazz}::${attribute}"

    def get_ast_dim_body_code(self, node: py2neo.Node) -> str:

        assert node[NODE_TYPE] == TYPE_DIM
        dim_body = self.parent.get_ast_child_node(self.parent.get_ast_child_node(node))[NODE_CODE]
        return dim_body

    def get_ast_dim_code(self, node: py2neo.Node) -> str:

        assert node[NODE_TYPE] == TYPE_DIM
        dim_body = self.parent.get_ast_node_code(self.parent.get_ast_ith_child_node(node, 0))
        dim_slice = self.parent.get_ast_node_code(self.parent.get_ast_ith_child_node(node, 1))
        if dim_slice == 'null':
            dim_slice = ''
        elif self.parent.get_ast_ith_child_node(node, 1)[NODE_TYPE] == TYPE_STRING:
            dim_slice = f"\"{dim_slice}\""
        logger.debug(
            f"DEBUGGING AST_DIM, {self.parent.get_ast_ith_child_node(node, 1)[NODE_TYPE]} => {dim_body}[{dim_slice}] ")
        return f"{dim_body}[{dim_slice}]"

    def get_ast_call_code(self, node: py2neo.Node) -> str:

        assert node[NODE_TYPE] == TYPE_CALL
        return self.parent.get_ast_child_node(self.parent.get_ast_child_node(node))[NODE_CODE]

    def get_ast_static_call_code(self, node: py2neo.Node) -> str:

        assert node[NODE_TYPE] == TYPE_STATIC_CALL
        ch_nodes = self.parent.find_ast_child_nodes(node)
        class_name_expr = self.parent.get_ast_child_node(ch_nodes[0])[NODE_CODE]
        if ch_nodes.__len__() >= 1:
            class_method_expr = ch_nodes[1][NODE_CODE]
        else:

            class_method_expr = "$" + self.parent.get_ast_child_node(self.parent.get_ast_ith_child_node(node, 1))[
                NODE_CODE]
        return f"{class_name_expr}::{class_method_expr}"

    def get_ast_class_const_code(self, node: py2neo.Node) -> str:

        assert node[NODE_TYPE] == TYPE_CLASS_CONST
        ch_nodes = self.parent.find_ast_child_nodes(node)
        class_name_expr = self.parent.get_ast_child_node(ch_nodes[0])[NODE_CODE]
        if ch_nodes.__len__() >= 1:
            class_method_expr = ch_nodes[1][NODE_CODE]
        else:

            class_method_expr = "$" + self.parent.get_ast_child_node(self.parent.get_ast_ith_child_node(node, 1))[
                NODE_CODE]
        return f"{class_name_expr}::{class_method_expr}"

    def get_ast_method_call_code(self, node: py2neo.Node) -> str:

        assert node[NODE_TYPE] == TYPE_METHOD_CALL
        if self.parent.get_ast_ith_child_node(node, 1)[NODE_TYPE] == TYPE_VAR:
            return self.parent.get_ast_ith_child_node(self.parent.get_ast_ith_child_node(node, 1), 0)[NODE_CODE]
        return self.parent.get_ast_ith_child_node(node, 1)[NODE_CODE]

    def find_variables(self, _node: py2neo.Node, target_type: Union[List, Set] = None) -> List[str]:

        if target_type is None:
            target_type = VAR_TYPES
            result = self.parent.filter_ast_child_nodes(_node=_node, node_type_filter=target_type)
            _res = [_ for _ in map(self.get_node_code, result)]
            return _res
        else:
            result = self.parent.filter_ast_child_nodes(_node=_node, node_type_filter=target_type)
            return list(set(_ for _ in map(self.get_node_code, result)))
