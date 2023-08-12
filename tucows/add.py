from typing import Callable
from os import path
from urllib import request

from psycopg.connection import Connection

from tucows.graph import parse, Graph


def add(connect_db: Callable[[], Connection], file: str):
    graph = read_graph(file)

    with connect_db() as conn:
        
        conn.execute("insert into graph (id, name) values (%s, %s);", (graph.id, graph.name))
        for node in graph.nodes:
            conn.execute("insert into node (graph_id, id, name) values (%s, %s, %s);", (graph.id, node.id, node.name))

        for edge in graph.edges:
            conn.execute(
                "insert into edge (graph_id, id, from_id, to_id, cost) values (%s, %s, %s, %s, %s);",
                (graph.id, edge.id, edge.from_node.id, edge.to_node.id, edge.cost)
            )


def read_graph(file: str) -> Graph:
    if path.exists(file):
        with open(file, "r") as f:
            return parse(f.read())

    print(file)
    with request.urlopen(file, timeout=5) as resp:
        return parse(resp.read().decode("utf-8"))
