import logging
import time

from apis.cache.thread_pool import *
from apis.graph_traversal import BaseGraphTraversal
from apis.vuln_model import *

logger = logging.getLogger(__name__)


class GlobalPDGForwardTraversal(BaseGraphTraversal):
    def __init__(self, *args, **kwargs):
        super(GlobalPDGForwardTraversal, self).__init__(*args, **kwargs)

        self.func_depth = {}
        self.max_func_depth = kwargs.get('max_func_depth', 3)
        self.func_all_var_cache = {}
        self.func_taint_label = {}

    def get_all_arg_var(self, node):
        if node[NODE_INDEX] in self.func_all_var_cache.keys():
            return self.func_all_var_cache[node[NODE_INDEX]]
        else:
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
            self.func_all_var_cache[node[NODE_INDEX]] = result
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


class GlobalPDGForwardTraversalWithModel(GlobalPDGForwardTraversal):

    def __init__(self, *args, **kwargs):
        self.vuln_type = kwargs.pop("vuln_type")
        use_prefetch = kwargs.pop("use_prefetch", False)
        super(GlobalPDGForwardTraversalWithModel, self).__init__(*args, **kwargs)
        self.cache_graph = self.analysis_framework.cache
        self.cache_graph.customize_storage['call_decl'] = {}
        self.cache_graph.customize_storage['call_decl_source'] = {}
        if use_prefetch:
            self.thread_pool = PrefetchPool.from_analyzer(self.analysis_framework, thread_count=10)
        else:
            self.thread_pool = PrefetchPool.from_analyzer(self.analysis_framework, thread_count=0)
        c_time = time.time()
        logger.info("")
        self.origin_node = self.find_origin(self.get_source_functions())
        self.terminal_node, self.sink_number = self.find_terminal(self.get_sink_functions())
        self.sanitizer = self.find_sanitizer(self.get_sanitizer_functions())
        self.get_call_return = lambda x: self.cache_graph.customize_storage['call_decl'].get(x, None)
        self.set_call_return = lambda k, v: self.cache_graph.customize_storage['call_decl'].__setitem__(k, v)
        self.node_without_cache_hit = []
        self.cache_hit = 0
        self.query_count = 0
        self.prefetch_hit = 0
        # wrapper
        self.origin = self.origin_node
        self.origin_node_id = [i[NODE_INDEX] for i in self.origin_node]
        self.terminal = [lambda x, *_args, **__kwargs: i[NODE_INDEX] for i in self.terminal_node]
        self.terminal_node_id = [i[NODE_INDEX] for i in self.terminal_node]

        logger.info(f"the number of origin is:" + str(len(self.origin)))
        logger.info(f"the number of terminal is:" + str(len(self.terminal)))

    def get_vuln_type(self):
        return VULN_TYPE_ID_TO_STRING.get(self.vuln_type)

    def get_source_functions(self):
        rt = POTENTIAL_SOURCE_MODEL
        return rt

    def get_sanitizer_functions(self):

        rt = BASIC_SANITIZE_FUNCTIONS
        if self.get_vuln_type() in EXTERNAL_SANITIZE_FUNCTIONS.keys():
            rt |= set(EXTERNAL_SANITIZE_FUNCTIONS[self.get_vuln_type()])

        logger.info(f"Confirm sanitize model :: {rt}")
        return rt

    def get_sink_functions(self):
        rt = POTENTIAL_SINK_MODEL[self.get_vuln_type()]
        logger.info(f"Confirm sink model :: {rt}")
        return rt

    def find_origin(self, origin_functions):
        user_input_nodes = []
        for origin_function in origin_functions:
            user_input_nodes.extend(
                self.analysis_framework.basic_step.match(**{NODE_CODE: origin_function,
                                                            }).all())
        origin_node = []
        for target_node in user_input_nodes:
            node = self.analysis_framework.get_ast_root_node(target_node)
            if node is not None and node[NODE_TYPE] == TYPE_ASSIGN:
                origin_node.append(node)

        return sorted(set(origin_node), key=lambda x: x[NODE_INDEX])

    def find_sanitizer(self, sanitize_function):
        target_nodes = []
        for sanitizer_function in sanitize_function:
            target_nodes.extend(
                self.analysis_framework.neo4j_graph.nodes.match(**{NODE_CODE: sanitizer_function, }).all())
        result_node = []
        for target_node in target_nodes:
            node = self.analysis_framework.ast_step.get_root_node(target_node)
            if node is not None:
                result_node.append(node)
        sanitizer_nodes_id = []
        for sanitizer_node in result_node:
            sanitizer_nodes_id.append(sanitizer_node[NODE_INDEX])
        return [lambda x, **kwargs: x[NODE_INDEX] in sanitizer_nodes_id]

    def find_terminal(self, terminal_functions):
        terminal_node = []
        sink_number = {}
        if self.get_vuln_type() == XSS:
            terminal_functions -= POTENTIAL_SINK_MODEL[XSS]
            target_nodes = self.analysis_framework.neo4j_graph.nodes.match(
                **{NODE_TYPE: TYPE_ECHO,
                   }).all()
            for target_node in target_nodes:
                node = self.analysis_framework.ast_step.get_root_node(target_node)
                if node is not None and \
                        self.analysis_framework.ast_step.filter_child_nodes(_node=node,
                                                                            node_type_filter=VAR_TYPES_EXCLUDE_CONST_VAR).__len__() >= 1:
                    terminal_node.append(node)
            target_nodes = self.analysis_framework.neo4j_graph.nodes.match(
                **{NODE_TYPE: TYPE_PRINT,
                   }).all()
            for target_node in target_nodes:
                node = self.analysis_framework.ast_step.get_root_node(target_node)
                if node is not None and \
                        self.analysis_framework.ast_step.filter_child_nodes(_node=node,
                                                                            node_type_filter=VAR_TYPES_EXCLUDE_CONST_VAR).__len__() >= 1:
                    terminal_node.append(node)
        elif self.get_vuln_type() == ARBITRARY_FILE_INCLUDE:
            terminal_functions -= POTENTIAL_SINK_MODEL[ARBITRARY_FILE_INCLUDE]
            target_nodes = self.analysis_framework.neo4j_graph.nodes.match(
                **{NODE_TYPE: TYPE_INCLUDE_OR_EVAL
                   }).all()
            for target_node in target_nodes:
                if target_node[NODE_FLAGS] == [FLAG_EXEC_EVAL]:
                    continue
                node = self.analysis_framework.ast_step.get_root_node(target_node)
                if node is not None and \
                        self.analysis_framework.ast_step.filter_child_nodes(_node=node,
                                                                            node_type_filter=VAR_TYPES_EXCLUDE_CONST_VAR).__len__() >= 1:
                    terminal_node.append(node)

        elif self.get_vuln_type() == ALL_SINK:
            terminal_functions -= POTENTIAL_SINK_MODEL[XSS]

            echo_sink = 0
            target_nodes = self.analysis_framework.neo4j_graph.nodes.match(
                **{NODE_TYPE: TYPE_ECHO,
                   }).all()
            for target_node in target_nodes:
                node = self.analysis_framework.ast_step.get_root_node(target_node)
                if node is not None and \
                        self.analysis_framework.ast_step.filter_child_nodes(_node=node,
                                                                            node_type_filter=VAR_TYPES_EXCLUDE_CONST_VAR).__len__() >= 1:
                    terminal_node.append(node)
                    echo_sink += 1
            sink_number['echo'] = echo_sink
            print_sink = 0
            target_nodes = self.analysis_framework.neo4j_graph.nodes.match(
                **{NODE_TYPE: TYPE_PRINT,
                   }).all()
            for target_node in target_nodes:
                node = self.analysis_framework.ast_step.get_root_node(target_node)
                if node is not None and \
                        self.analysis_framework.ast_step.filter_child_nodes(_node=node,
                                                                            node_type_filter=VAR_TYPES_EXCLUDE_CONST_VAR).__len__() >= 1:
                    terminal_node.append(node)
                    print_sink += 1
            sink_number['print'] = print_sink
            terminal_functions -= POTENTIAL_SINK_MODEL[ARBITRARY_FILE_INCLUDE]
            terminal_functions -= {'eval'}
            include_sink = 0
            eval_sink = 0
            target_nodes = self.analysis_framework.neo4j_graph.nodes.match(
                **{NODE_TYPE: TYPE_INCLUDE_OR_EVAL
                   }).all()
            for target_node in target_nodes:
                node = self.analysis_framework.ast_step.get_root_node(target_node)
                if node is not None and \
                        self.analysis_framework.ast_step.filter_child_nodes(_node=node,
                                                                            node_type_filter=VAR_TYPES_EXCLUDE_CONST_VAR).__len__() >= 1:
                    terminal_node.append(node)
                    if target_node[NODE_FLAGS] == [FLAG_EXEC_EVAL]:
                        eval_sink += 1
                    else:
                        include_sink += 1
            sink_number['eval'] = eval_sink
            sink_number['include'] = include_sink

        for sink_functions in terminal_functions:
            func_sink = 0
            target_nodes = self.analysis_framework.neo4j_graph.nodes.match(
                **{NODE_CODE: sink_functions,
                   }).all()
            for target_node in target_nodes:
                # if self.analysis_framework.ast_step.find_parent_nodes(target_node)[0][NODE_TYPE] != TYPE_NAME:
                #     continue
                node = self.analysis_framework.ast_step.get_root_node(target_node)
                # if node is not None and \
                #         self.analysis_framework.ast_step.filter_child_nodes(_node=node,
                #                                                             node_type_filter=VAR_TYPES_EXCLUDE_CONST_VAR).__len__() >= 1:
                if node is not None:
                    terminal_node.append(node)
                    func_sink += 1
            sink_number[sink_functions] = func_sink

        return terminal_node, sink_number
