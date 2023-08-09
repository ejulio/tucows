from typing import List
from dataclasses import dataclass
from io import StringIO

from lxml import etree

class InvalidGraph(ValueError):
    pass

@dataclass
class Node:
    id: str
    name: str

@dataclass
class Edge:
    id: str
    from_node: Node
    to_node: Node
    cost: int

@dataclass
class Graph:
    id: str
    name: str
    edges: List[Edge]
    nodes: List[Node]

def parse(xml: str) -> Graph:
    doc = etree.parse(StringIO(xml))

    try:
        schema = etree.XMLSchema(etree.parse(open("tucows/graph_schema.xsd")))
        schema.assertValid(doc)
    except etree.DocumentInvalid as e:
        raise InvalidGraph(e)

    root = doc.getroot()
    nodes = list(map(_parse_node, root.xpath("nodes/node")))
    
    id_to_node = dict()
    for n in nodes:
        if n.id in id_to_node:
            raise InvalidGraph(f"node id {n.id} was already defined")
        id_to_node[n.id] = n

    edges = [_parse_edge(elem, id_to_node) for elem in root.xpath("edges/edge")]

    return Graph(
        id=root.xpath("id/text()")[0],
        name=root.xpath("name/text()")[0],
        nodes=nodes,
        edges=edges,
    )

def _parse_node(elem) -> Node:
    return Node(
        id=elem.xpath("id/text()")[0],
        name=elem.xpath("name/text()")[0],
    )

def _parse_edge(elem, id_to_node) -> Edge:
    edge_id = elem.xpath("id/text()")[0]

    from_id = elem.xpath("from/text()")[0]
    if from_id not in id_to_node:
        raise InvalidGraph(f"from {from_id} in edge {edge_id} is not defined in <nodes>")

    to_id = elem.xpath("to/text()")[0]
    if to_id not in id_to_node:
        raise InvalidGraph(f"to {to_id} in edge {edge_id} is not defined in <nodes>")
    
    cost = 0
    cost_str = elem.xpath("cost/text()")
    if cost_str:
        cost_str = cost_str[0]
        cost = float(cost_str)

    return Edge(
        id=edge_id,
        from_node=id_to_node[from_id],
        to_node=id_to_node[to_id],
        cost=cost,
    )