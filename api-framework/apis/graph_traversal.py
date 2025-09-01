import py2neo

from abc import ABCMeta, ABC, abstractclassmethod, abstractmethod, abstractproperty
from typing import Dict, Set, Union, List, Callable
from py2neo import Node, Relationship
import networkx as nx
from collections import deque
from apis.analysis_framework import AnalysisFramework
from apis.graph_traversal_recorder import BaseRecorder, GraphTraversalRecorder
from apis.const import *

DEFAULT_SANTITZER = lambda *args, **kwargs: False  # return True, treat as sanitizer , stack the traversal

__all__ = ["BaseGraphTraversal",
           "ControlGraphForwardTraversal", "GlobalControlGraphForwardTraversal",
           "GlobalProgramDependencyGraphBackwardTraversal", "ProgramDependencyGraphBackwardTraversal"]

ORIGIN_RULE = 0xcf01
TERMINAL_RULE = 0xcf02
SANITIZER_RULE = 0xcf03


class BaseGraphTraversal(object):

    def __init__(self, analysis_framework: AnalysisFramework,
                 origin: List[Callable] = None,
                 terminal: List[Callable] = None,
                 sanitizer: List[Callable] = None,
                 recorder: Callable = None):

        if sanitizer is None:
            sanitizer = [DEFAULT_SANTITZER]
        if origin is None:
            origin = []
        if terminal is None:
            terminal = []
        if recorder is None:
            recorder = GraphTraversalRecorder
        self.analysis_framework: AnalysisFramework = analysis_framework
        self.cache_graph = self.analysis_framework.cache

        self.__visit_node_pool: Dict = {}
        self._origin: List[Callable] = origin
        self.origin = []
        self.terminal: List[Callable] = terminal
        self.sanitizer: List[Callable] = sanitizer
        self.recorder: BaseRecorder = recorder(analysis_framework)
        self._result: List[Node] = []

        self.traversal_param_list = {}
        self.sanitizer_param_list = {}
        self.terminal_param_list = {}

    def get_record(self):

        return self.recorder.storage_graph

    def get_result(self):

        return self._result

    @abstractmethod
    def traversal(self, current_node, *args, **kwargs):
        return self.analysis_framework.find_cfg_successors(current_node)

    def init_traversal(self):

        if self.origin.__len__() != 0:
            return True

        if self._origin.__len__() == 0:
            raise IndexError("self.origin should not be empty")
        if isinstance(self._origin[0], py2neo.Node):
            self.origin = self._origin  # type:List[py2neo.Node]
        else:
            for origin_func in self._origin:
                self.origin.extend(origin_func(self.analysis_framework))

    def run(self):

        self.__visit_node_pool = {}
        self.init_traversal()

        query: deque[py2neo.Node] = deque()
        for o in self.origin:
            query.append(o)
            self.__visit_node_pool[o[NODE_INDEX]] = {}
            o['origin'] = o[NODE_INDEX]
            self.recorder.record_origin(o)

        while query.__len__() != 0:
            current_node = query.popleft()
            next_nodes = []
            candidate_nodes = []

            if current_node['origin'] in self.__visit_node_pool.keys() \
                    and current_node.identity in self.__visit_node_pool[current_node['origin']].keys():
                self.__visit_node_pool[current_node['origin']][current_node.identity] += 1
                continue
            elif current_node['origin'] not in self.__visit_node_pool.keys():
                self.__visit_node_pool[current_node['origin']] = {}
                self.__visit_node_pool[current_node['origin']][current_node.identity] = 1
            else:
                self.__visit_node_pool[current_node['origin']][current_node.identity] = 1

            node__ = self.traversal(current_node, **self.traversal_param_list)
            for node_ in node__:
                node_['origin'] = current_node['origin']
            candidate_nodes.extend(node__)

            for candidate_node in candidate_nodes:

                _sanitize_flag = 0b0
                _terminal_flag = 0b0
                for index, rule in enumerate(self.sanitizer, start=0):
                    _sanitize_flag |= 0 if rule(candidate_node, **self.sanitizer_param_list) else (
                            1 << index)
                if _sanitize_flag == (1 << self.sanitizer.__len__()) - 1:
                    for index, rule in enumerate(self.terminal, start=0):
                        _terminal_flag |= (1 << index) if rule(candidate_node,
                                                               **self.terminal_param_list) else 0

                    if _terminal_flag > 0:
                        self._result.append(candidate_node)
                    next_nodes.append(candidate_node)

            for next_node in next_nodes:
                if self.recorder.record(current_node, next_node):
                    query.append(next_node)


class ProgramDependencyGraphBackwardTraversal(BaseGraphTraversal):

    def __init__(self, *args, **kwargs):

        super(ProgramDependencyGraphBackwardTraversal, self).__init__(*args, **kwargs)

    def traversal(self, node, *args, **kwargs):

        return self.analysis_framework.find_pdg_def_nodes(node)


class ControlGraphForwardTraversal(BaseGraphTraversal):


    def __init__(self, *args, **kwargs):

        super(ControlGraphForwardTraversal, self).__init__(*args, **kwargs)
        self.loop_structure_instance = {}

    def __switch(self, next_node):
        if next_node in self.loop_structure_instance.keys():
            return self.__switch(self.loop_structure_instance[next_node])
        else:
            return next_node

    def traversal(self, node, *args, **kwargs):

        next_nodes = self.analysis_framework.find_cfg_successors(node)
        result = []
        for next_node in next_nodes:
            parent_node = self.analysis_framework.get_ast_parent_node(node)
            if parent_node[NODE_TYPE] == TYPE_FOR and \
                    self.analysis_framework.get_ast_ith_child_node(parent_node, 2) \
                    not in self.loop_structure_instance.keys():
                self.loop_structure_instance[
                    self.analysis_framework.get_ast_ith_child_node(parent_node, 2)
                ] = self.analysis_framework.find_cfg_successors(
                        self.analysis_framework.get_ast_ith_child_node(parent_node, 1)
                )[1]
            elif parent_node[NODE_TYPE] == TYPE_WHILE:
                self.loop_structure_instance[node] = self.analysis_framework.find_cfg_successors(node)[1]
            elif node[NODE_TYPE] == TYPE_FOREACH:
                self.loop_structure_instance[node] = self.analysis_framework.find_cfg_successors(node)[1]
            if next_node[NODE_INDEX] < node[NODE_INDEX]:

                if next_node in self.loop_structure_instance.keys():
                    next_node = self.__switch(next_node)
                else:
                    print("Problem not solved")

            result.append(next_node)
        return result


class GlobalProgramDependencyGraphBackwardTraversal(BaseGraphTraversal):

    def __init__(self, *args, **kwargs):

        super(GlobalProgramDependencyGraphBackwardTraversal, self).__init__(*args, **kwargs)
        self.func_depth = {}
        self.max_func_depth = kwargs.get('max_func_depth', 3)
        self.sanitizer_param_list = {"analysis_framework": self.analysis_framework}


    def traversal(self, node, *args, **kwargs):
        if node[NODE_FUNCID] not in self.func_depth:
            self.func_depth[node[NODE_FUNCID]] = 0
        if self.func_depth[node[NODE_FUNCID]] >= self.max_func_depth:
            return []

        result = []
        define_nodes = self.analysis_framework.find_pdg_def_nodes(node)
        result.extend(define_nodes)

        if node[NODE_TYPE] != TYPE_ASSIGN:
            return result
        call_nodes = self.analysis_framework.filter_ast_child_nodes(
                self.analysis_framework.get_ast_ith_child_node(node, 1),
                node_type_filter=[TYPE_CALL, TYPE_METHOD_CALL, TYPE_STATIC_CALL]
        )
        for call_node in call_nodes:
            callable_node = self.analysis_framework.find_cg_decl_nodes(call_node)
            if callable_node:
                callable_node = callable_node[0]

                return_nodes = self.analysis_framework.ast_step.find_function_return_expr(callable_node)
                for return_node in return_nodes:
                    if return_node[NODE_FUNCID] not in self.func_depth:
                        self.func_depth[return_node[NODE_FUNCID]] = self.func_depth[node[NODE_FUNCID]] + 1
                result.extend(return_nodes)
        return result


class GlobalControlGraphForwardTraversal(ControlGraphForwardTraversal):


    def __init__(self, *args, **kwargs):

        super(ControlGraphForwardTraversal, self).__init__(*args, **kwargs)
        self.func_depth = {}
        self.max_func_depth = kwargs.get('max_func_depth', 3)
        self.loop_structure_instance = {}

    def traversal(self, node, *args, **kwargs):

        if node[NODE_FUNCID] not in self.func_depth:
            self.func_depth[node[NODE_FUNCID]] = 0
        if self.func_depth[node[NODE_FUNCID]] >= self.max_func_depth:
            return []


        result = []

        next_nodes = self.analysis_framework.find_cfg_successors(node)
        for next_node in next_nodes:
            parent_node = self.analysis_framework.get_ast_parent_node(node, ignore_error_flag=True)
            if parent_node is None: parent_node = {NODE_TYPE: TYPE_NULL}
            if parent_node[NODE_TYPE] == TYPE_FOR and \
                    self.analysis_framework.get_ast_ith_child_node(parent_node, 2) \
                    not in self.loop_structure_instance.keys():
                self.loop_structure_instance[
                    self.analysis_framework.get_ast_ith_child_node(parent_node, 2)
                ] = self.analysis_framework.find_cfg_successors(
                        self.analysis_framework.get_ast_ith_child_node(parent_node, 1)
                )[1]
            elif parent_node[NODE_TYPE] == TYPE_WHILE:
                self.loop_structure_instance[node] = self.analysis_framework.find_cfg_successors(node)[1]
            elif node[NODE_TYPE] == TYPE_FOREACH:
                self.loop_structure_instance[node] = self.analysis_framework.find_cfg_successors(node)[1]
            if next_node[NODE_INDEX] < node[NODE_INDEX]:

                if next_node in self.loop_structure_instance.keys():
                    next_node = self.__switch(next_node)
                else:
                    print("Problem not solved")

            result.append(next_node)

        call_nodes = self.analysis_framework.filter_ast_child_nodes(node,
                                                                    node_type_filter=[TYPE_CALL, TYPE_METHOD_CALL,
                                                                                      TYPE_STATIC_CALL])
        for call_node in call_nodes:
            callable_node = self.analysis_framework.find_cg_decl_nodes(call_node)
            if callable_node:
                callable_node = callable_node[0]

                first_elems = self.analysis_framework.ast_step.find_function_entrance_expr(callable_node)
                assert first_elems.__len__() == 1
                for first_elem in first_elems:
                    if first_elem[NODE_FUNCID] not in self.func_depth:
                        self.func_depth[first_elem[NODE_FUNCID]] = self.func_depth[node[NODE_FUNCID]] + 1
                result.extend(first_elems)
        return result


class GlobalPDGForwardTraversal(BaseGraphTraversal):
    def __init__(self, *args, **kwargs):
        super(GlobalPDGForwardTraversal, self).__init__(*args, **kwargs)

        self.func_depth = {}
        self.max_func_depth = kwargs.get('max_func_depth', 3)

    def get_all_arg_var(self, node):
        assert node[NODE_TYPE] in [TYPE_CALL, TYPE_METHOD_CALL, TYPE_STATIC_CALL, TYPE_NEW]
        result = {}
        args_nodes = self.analysis_framework.filter_ast_child_nodes(
                node,
                node_type_filter=[TYPE_ARG_LIST]
        )
        for args_node in args_nodes:
            var_node = self.analysis_framework.filter_ast_child_nodes(
                    args_node,
                    node_type_filter=[TYPE_VAR]
            )
            for var in var_node:
                child_num = var[NODE_CHILDNUM]
                code = self.analysis_framework.code_step.get_node_code(var)
                result[code] = child_num
        return result

    def match_cg_dataflow(self, call_node, child_num):
        decl_nodes = self.analysis_framework.find_cg_decl_nodes(call_node)
        result = []
        for decl_node in decl_nodes:
            param_nodes = self.analysis_framework.filter_ast_child_nodes(
                    decl_node,
                    node_type_filter=[TYPE_PARAM]
            )
            for param_node in param_nodes:
                if param_node[NODE_CHILDNUM] == child_num:
                    use_node = self.analysis_framework.find_pdg_use_nodes(param_node)
                    result.extend(use_node)
        return result

    def traversal(self, node, *args, **kwargs):
        if node[NODE_FUNCID] not in self.func_depth:
            self.func_depth[node[NODE_FUNCID]] = 0
        if self.func_depth[node[NODE_FUNCID]] >= self.max_func_depth:
            return []
        result = []

        use_node = self.analysis_framework.pdg_step.find_use_nodes(node)
        result.extend(use_node)
        if node['taint_var'] != '':
            if node[NODE_TYPE] not in [TYPE_CALL, TYPE_METHOD_CALL, TYPE_STATIC_CALL, TYPE_NEW]:
                call_nodes = self.analysis_framework.filter_ast_child_nodes(
                        node,
                        node_type_filter=[TYPE_CALL, TYPE_METHOD_CALL, TYPE_STATIC_CALL, TYPE_NEW]
                )
            else:
                call_nodes = [node]
            for call_node in call_nodes:
                arg_list = self.get_all_arg_var(call_node)
                for key in arg_list.keys():
                    if key == f"${node['taint_var']}":
                        result_node = self.match_cg_dataflow(call_node, arg_list[key])
                        result.extend(result_node)
        return result

