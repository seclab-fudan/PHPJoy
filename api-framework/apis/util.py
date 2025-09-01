from apis.cache.prefetch_task import *

def get_all_arg_var(analysis_framework, node):
    result = {}
    args_nodes = analysis_framework.filter_ast_child_nodes(
            node,
            node_type_filter=[TYPE_ARG_LIST]
    )
    for args_node in args_nodes:
        var_node = analysis_framework.filter_ast_child_nodes(
                args_node,
                node_type_filter=[TYPE_VAR]
        )
        for var in var_node:
            child_num = var[NODE_CHILDNUM]
            code = analysis_framework.code_step.get_node_code(var)
            result[code] = child_num
    return result
