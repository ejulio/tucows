from dataclasses import dataclass
import json
import sys
from typing import Callable, List, Iterable

from psycopg.connection import Connection


FIND_PATH_QUERY = """with recursive graph_traversal (graph_id, from_id, to_id, node_path, path_cost, has_cycle) as (
	select
        graph_id,
		from_id,
		to_id,
		concat(',', from_id, ',', to_id, ',') as node_path,
		cost as path_cost,
		(case when from_id = to_id then true else false end) as has_cycle
	from
		edge
    where
        graph_id = %(graph)s
        and
        from_id = %(from)s
	union all
	select
        e.graph_id,
		e.from_id,
		e.to_id,
		concat(gt.node_path, e.to_id, ',') as node_path,
		gt.path_cost + e.cost as path_cost,
		(case 
			when gt.has_cycle then true
			when gt.node_path like concat('%%,', e.to_id, ',%%') then true
			else false 
		end) as has_cycle
	from
		graph_traversal as gt
		join edge as e on e.from_id = gt.to_id and e.graph_id = gt.graph_id
	where
		not gt.has_cycle
		or
		e.to_id = %(to)s
)
select
	trim(',' from gt.node_path) as path,
	gt.path_cost as cost
from
	graph_traversal as gt
where
	gt.to_id = %(to)s
	and
	not gt.has_cycle;"""


@dataclass
class Query:
    type_: str
    graph: str
    from_node: str
    to_node: str


@dataclass
class GraphPath:
    from_node: str
    to_node: str
    nodes: List[str]
    cost: float


def query(connect_db: Callable[[], Connection]):
    answers = []
    with connect_db() as conn:
        for query in read_queries():
            if query.type_ == "cheapest":
                answers.append(find_cheapest_path(conn, query))
            elif query.type_ == "paths":
                answers.append(find_all_paths(conn, query))
            else:
                raise ValueError(f"invalid query type {query.type_}")

    print(json.dumps({"answers": answers}))


def read_queries() -> Iterable[Query]:
    parsed = json.loads(sys.stdin.read())
    if "queries" not in parsed or not parsed["queries"]:
        raise ValueError("expected at least one entry in 'queries'")

    for q in parsed["queries"]:
        if len(q) > 1:
            raise ValueError("query must have either cheapest or paths")

        type_ = list(q.keys())[0]
        yield Query(
            type_=type_,
            graph=q[type_]["graph"],
            from_node=q[type_]["start"],
            to_node=q[type_]["end"],
        )


def find_cheapest_path(conn: Connection, query: Query):
    cheapest = None
    for path in query_all_paths(conn, query):
        if cheapest is None:
            cheapest = path
        elif path.cost < cheapest.cost:
            cheapest = path

    return {
        "cheapest": {
            "from": query.from_node,
            "to": query.to_node,
            "path": cheapest.nodes if cheapest else False
        }
    }


def find_all_paths(conn: Connection, query: Query):
    paths = []
    for path in query_all_paths(conn, query):
        paths.append(path.nodes)

    return {
        "paths": {
            "from": query.from_node,
            "to": query.to_node,
            "paths": paths
        }
    }


def query_all_paths(conn: Connection, query: Query) -> Iterable[GraphPath]:
    params = {"graph": query.graph, "from": query.from_node, "to": query.to_node}
    for result in conn.execute(FIND_PATH_QUERY, params):
        yield GraphPath(
            from_node=query.from_node,
            to_node=query.to_node,
            nodes=result[0].split(","),
            cost=result[1],
        )
