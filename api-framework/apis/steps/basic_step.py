from typing import List, Union, Dict, Set
import py2neo
from apis.const import *
from .abstract_step import AbstractStep


class BasicStep(AbstractStep):

    def __init__(self, parent):

        super().__init__(parent, "basic_step")
        self.neo4j_graph = parent.neo4j_graph

    def run(self, query) -> py2neo.NodeMatch:

        return self.neo4j_graph.run(query)

    def run_and_fetch_one(self, query) -> py2neo.NodeMatch:

        for i in self.neo4j_graph.run(query):
            return i
        return None

    def match(self, *args, **kwargs) -> py2neo.NodeMatch:

        return self.neo4j_graph.nodes.match(*args, **kwargs)

    def match_first(self, *args, **kwargs) -> py2neo.Node:

        return self.neo4j_graph.nodes.match(*args, **kwargs).first()

    def match_relationship(self, *args, **kwargs) -> py2neo.RelationshipMatch:

        return self.neo4j_graph.relationships.match(*args, **kwargs)

    def match_first_relationship(self, *args, **kwargs) -> py2neo.Relationship:

        return self.neo4j_graph.relationships.match(*args, **kwargs).first()

    def get_node_itself(self, _id: int) -> py2neo.Node:

        if self.parent._use_cache and self.parent.cache.get_node(_id):
            return self.parent.cache.get_node(_id)
        else:
            node = self.neo4j_graph.nodes.match(id=_id).limit(1).first()
            if self.parent._use_cache:
                self.parent.cache.add_node(node)
            return node

    def get_node_itself_by_identity(self, _id: int):

        return self.neo4j_graph.nodes.get(identity=_id)
