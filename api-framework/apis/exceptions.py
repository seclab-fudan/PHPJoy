class Neo4jEmptyError(Exception):
    def __init__(self, buffer):
        self.buffer = buffer

    def __str__(self):
        return "neo4j is empty   {} ,\n" \
               " please inform wzw to check out  !".format(
            self.buffer)


class Neo4jInitFormatError(Exception):
    def __init__(self, buffer):
        self.buffer = buffer

    def __str__(self):
        return f"Init Neo4j got input format error , the init option should be Dict or str ," \
               f" which owes special format , or neo4j.graph object , \ngot {self.buffer} instead"


class Neo4jNodeListIndexError(Exception):
    def __init__(self, buffer, index):
        self.buffer = buffer
        self.index = index

    def __str__(self):
        return f"[!] Node List Index {self.index} error \n Get input node {self.buffer}"


class Neo4jQuickCodeGenerationError(Exception):
    def __init__(self, buffer):
        self.buffer = buffer

    def __str__(self):
        return f'[!] {self.buffer} not implement; \n Please import shaobaobaoer to fix bugs'


class GraphTraversalInitError(Exception):
    def __init__(self, buffer):
        self.buffer = buffer

    def __str__(self):
        return f'[!] The GraphTraversal Class Init error; \n {self.buffer}'
