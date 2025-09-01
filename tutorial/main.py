import argparse
import json
import logging
# use apis as core library
import sys
import time

sys.path.append("../api-framework")
from apis.cache.prefetch_task_impl import CallDeclTask, PDGUseTask
from apis.cache.thread_pool import *
from apis.graph_traversal_model import GlobalPDGForwardTraversalWithModel
from apis.graph_traversal_recorder import ResultRecorder
from apis.vuln_model import VULN_TYPE_ID_TO_STRING
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(prog="phpjoy-cli")
parser.add_argument("-vt", "--vuln-type", dest='vuln_type', action="store", type=int, default=-1, metavar="VULN_TYPE",
                    help="INPUT VULN TYPE")
parser.add_argument("-o", "--output", dest='output', action="store", type=str, default="./", metavar="OUTPUT_PATH",
                    help="INPUT OUTPUT PATH")
parser.add_argument("-1", "--map-key", dest='map_key', action="store", type=str, default="example", metavar="MAP_KEY",
                    help="INPUT MAP KEY")
ENTRANCE_PARAMS = parser.parse_args()


class ForwardTraversalWithPrefetch(GlobalPDGForwardTraversalWithModel):
    def __init__(self, *args, **kwargs):
        super(ForwardTraversalWithPrefetch, self).__init__(*args, **kwargs)
        self.node_traversal_count = 0

    def traversal(self, node, *args, **kwargs):
        self.node_traversal_count += 1
        if node.get(NODE_FUNCID) not in self.func_depth:
            self.func_depth[node[NODE_FUNCID]] = 0
        if self.func_depth[node[NODE_FUNCID]] >= self.max_func_depth:
            return []
        result = []

        use_node = self.analysis_framework.pdg_step.find_use_nodes(node)
        result.extend(use_node)

        taint_var = node.get('taint_var', '')
        if taint_var != '':
            self.query_count += 1
            cache_key = node[NODE_INDEX]
            cached_decl = self.cache_graph.customize_storage['call_decl'].get(cache_key, {})
            cached_source_map = self.cache_graph.customize_storage['call_decl_source'].get(cache_key, {})

            if cached_decl.get(taint_var) is not None:
                result.extend(cached_decl[taint_var])
                self.cache_hit += 1
                if cached_source_map.get(taint_var) == 'prefetch':
                    self.prefetch_hit += 1
            else:
                res = []
                if node[NODE_TYPE] not in [TYPE_CALL, TYPE_METHOD_CALL, TYPE_STATIC_CALL, TYPE_NEW]:
                    call_nodes = self.analysis_framework.filter_ast_child_nodes(
                        node,
                        node_type_filter=[TYPE_CALL, TYPE_METHOD_CALL, TYPE_STATIC_CALL, TYPE_NEW]
                    )
                else:
                    call_nodes = [node]

                for call_node in call_nodes:
                    arg_list = self.get_all_arg_var(call_node)
                    target_key = f"${taint_var}"
                    for key, arg_node in arg_list.items():
                        if key == target_key:
                            result_node = self.match_cg_dataflow(call_node, arg_node)
                            res.extend(result_node)

                if self.cache_graph.customize_storage['call_decl'].get(cache_key) is None:
                    self.cache_graph.customize_storage['call_decl'][cache_key] = {}
                    self.cache_graph.customize_storage['call_decl_source'][cache_key] = {}

                self.cache_graph.customize_storage['call_decl'][cache_key][taint_var] = res
                self.cache_graph.customize_storage['call_decl_source'][cache_key][taint_var] = 'traversal'
                result.extend(res)

        self.thread_pool.put_task(PDGUseTask(cache_graph=self.cache_graph, node=result))
        for node_item in result:
            self.thread_pool.put_task(CallDeclTask(cache_graph=self.cache_graph, node=node_item))

        return result


class PHPJoyEntrance(object):
    def __init__(self):
        self.__version = "v 0.1"
        self.cli_input = ENTRANCE_PARAMS
        self.config = None

    def traversal_with_prefetch(self):
        start_time = time.time()
        cache_graph = BasicCacheGraph()

        with open("neo4j_configure_map.json", "r") as f:
            NEO4J_CONFIGURE_MAP = json.load(f)

        config = NEO4J_CONFIGURE_MAP.get(self.cli_input.map_key)
        if not config:
            raise ValueError(f"Map key '{self.cli_input.map_key}' not found in neo4j_configure_map.json")

        analysis_framework = AnalysisFramework.from_dict(config, cache_graph=cache_graph)
        traversal = ForwardTraversalWithPrefetch(
            analysis_framework=analysis_framework,
            recorder=ResultRecorder,
            use_prefetch=True,
            vuln_type=self.cli_input.vuln_type
        )

        traversal.run()

        result = traversal.recorder.get_report(
            origin_ids=traversal.origin_node_id,
            terminal_ids=traversal.terminal_node_id,
            analysis_framework=analysis_framework
        )
        logger.info(f"find {len(result)} taint path for vuln_type {self.cli_input.vuln_type}({VULN_TYPE_ID_TO_STRING.get(self.cli_input.vuln_type)})")
        json.dump(
            fp=open( f"{self.cli_input.output}-{self.cli_input.vuln_type}.json", "w"),
            obj=result
        )

if __name__ == "__main__":
    entrance = PHPJoyEntrance()
    entrance.traversal_with_prefetch()