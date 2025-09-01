from apis.cache.prefetch_task import *
from apis.util import get_all_arg_var


def match_CG_dataflow(analysis_framework, call_node, child_num):
    decl_nodes = analysis_framework.find_cg_decl_nodes(call_node)
    result = []
    for decl_node in decl_nodes:
        param_nodes = analysis_framework.filter_ast_child_nodes(
            decl_node,
            node_type_filter=[TYPE_PARAM]
        )
        for param_node in param_nodes:
            if param_node[NODE_CHILDNUM] == child_num:
                use_node = analysis_framework.find_pdg_use_nodes(param_node)
                result.extend(use_node)
    return result


class CallDeclTask(AbstractPrefetchTask):
    def __init__(self, **kwargs):
        analysis_framework = kwargs.pop('analysis_framework', None)
        cache_graph = kwargs.pop('cache_graph', None)
        super(CallDeclTask, self).__init__(analysis_framework=analysis_framework, cache_graph=cache_graph)
        self.node = kwargs.pop('node', None)

    def do_task(self):
        if self.cache_graph.customize_storage['call_decl'].get(self.node[NODE_INDEX], None) is not None and \
                self.cache_graph.customize_storage['call_decl'][self.node[NODE_INDEX]].get(
                    self.node['taint_var'], None) is not None:
            return
        result = []
        if self.node['taint_var'] != '':
            if self.node[NODE_TYPE] not in [TYPE_CALL, TYPE_METHOD_CALL, TYPE_STATIC_CALL, TYPE_NEW]:
                call_nodes = self.analysis_framework.filter_ast_child_nodes(
                    self.node,
                    node_type_filter=[TYPE_CALL, TYPE_METHOD_CALL, TYPE_STATIC_CALL, TYPE_NEW]
                )
            else:
                call_nodes = [self.node]
            for call_node in call_nodes:
                arg_list = get_all_arg_var(self.analysis_framework, call_node)
                for key in arg_list.keys():
                    if key == f"${self.node['taint_var']}":
                        result_node = match_CG_dataflow(self.analysis_framework, call_node, arg_list[key])
                        result.extend(result_node)
        if self.cache_graph.customize_storage['call_decl'].get(self.node[NODE_INDEX], None) is None:
            self.cache_graph.customize_storage['call_decl'][self.node[NODE_INDEX]] = {}
            self.cache_graph.customize_storage['call_decl_source'][self.node[NODE_INDEX]] = {}
        self.cache_graph.customize_storage['call_decl'][self.node[NODE_INDEX]][
            self.node['taint_var']] = result
        self.cache_graph.customize_storage['call_decl_source'][self.node[NODE_INDEX]][
            self.node['taint_var']] = 'prefetch'


class PDGUseTask(AbstractPrefetchTask):
    def __init__(self, **kwargs):
        cache_graph = kwargs.pop('cache_graph', None)
        super(PDGUseTask, self).__init__(cache_graph=cache_graph)
        self.nodes = kwargs.pop('node', None)

    def do_task(self):
        for node in self.nodes:
            if self.cache_graph.get_pdg_outflow(node) is None:
                rels = self.analysis_framework.neo4j_graph.relationships.match(nodes=[node, None],
                                                                               r_type=DATA_FLOW_EDGE, ).all()
                self.cache_graph.add_pdg_outflow(node, rels, source='prefetch')
