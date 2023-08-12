# Tucows test

## Running

### Postgres

You'll need `postgres` as it is the DB I used.
I could have used some ORM like `SQLAlchemy`, but decided to go raw with just `postgres` here.

```
docker pull postgres
docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres
```

### Build the project docker image

```
docker build -t tucows .
```

### Run the container

The command below will run the `tucows` image built above, linking it to the `postgres` instance started above.
The current working directory is mounted in the container so that any new files created in the directory show up in the container.
This is useful if you want to add a graph from a local file instead of an URL.

```
docker run --link postgres -v ${PWD}:/usr/tucows -it tucows /bin/bash
```

### Run `poetry` shell

```
poetry shell
```

### Run tasks

Connection string format `postgresql://user:password@host:port/dbname`. Example of a connection string
```
postgresql://postgres:postgres@postgres:5432/postgres
```

Parse and add graph to the database
```
python main.py -a=<path or url to file> --db-connection=<connection string>
```

Query for paths and cheapest path. This will read from `stdin`.
When done `CMD+d` or `CTRL+d` to signal `EOF`.

```
python main.py -q --db-connection=<connection string>
```

### Unit tests

There's a small suite of unit tests that can be run with `pytest` within `poetry shell`.

## Tasks

1. [x] Open/Download the file
2. [x] Parse graph
`lxml` was used just because of XSD validation.
I think this was a simple solution to validate the XML file, instead of writing the rules in code.
Some other validations had to be done in code, like unique names, as they would be a bit hard to do in XSD.
Though `lxml` doesn't rovide a good interface to map between XML and python objects, so mapping was manual through XPaths.
An alternative could be to use another library, but since the mapping was fairly simple, I opted to make it by hand.
The trade-off for validation is that the validation seemed better in XSD, so the extra library was a valid choice.

3. [x] SQL Schema

```
create table graph (
	id varchar(100) primary key,
	name varchar(500) not null
);

create table node (
	id varchar(100),
	graph_id varchar(100) references graph(id),
	name varchar(500) not null,
	primary key (graph_id, id)
);

create table edge (
	id varchar(100),
	graph_id varchar(100) references graph(id),
	from_id varchar(100),
	to_id varchar(100),
	cost float not null,
	foreign key (graph_id, from_id) references node(graph_id, id),
	foreign key (graph_id, to_id) references node(graph_id, id)
);
```

There's nothing special in this schema. There's one table for each entity (`Graph`, `Node`, `Edge`) and their IDs are the ones provided in the XML file.
So, for each entity the id is a string of size 100 chars (which seems enough).
The `Node` has a composite primary key, composed by the graph id and its own id.
Because of this composite id, the edge foreign key also needs to be composite.
Names are required in the XML file, so they can't be null.
Cost is not null because it's default value when parsing the graph was suggested to 0, so in the DB it won't be null.

4. [x] SQL Query

```
with recursive graph_traversal as (
	select
        graph_id,
		from_id,
		to_id,
		concat(',', from_id, ',', to_id, ',') as nodes,
		(case when from_id = to_id then 1 else 0 end) as has_cycle
	from
		edge
    where
        graph_id = <GRAPH ID HERE>
	union all
	select
        e.graph_id,
		e.from_id,
		e.to_id,
		concat(graph_traversal.nodes, e.to_id, ',') as nodes,
		(case when graph_traversal.nodes like concat('%,', e.to_id, ',%') then 1 else 0 end) as has_cycle
	from
		graph_traversal
		join edge e on e.from_id = graph_traversal.to_id and e.graph_id = graph_traversal.graph_id
	where
		graph_traversal.has_cycle = 0
)
select exists(select 1 from graph_traversal where has_cycle = 1 limit 1) as has_cycle;
```

Below you can find some sample data I used for testing.

```
-- cycle 1
insert into graph (id, name) values ('cycle1', 'graph');

insert into node (graph_id, id, name) values ('cycle1', 'a', 'a');
insert into node (graph_id, id, name) values ('cycle1', 'b', 'b');
insert into node (graph_id, id, name) values ('cycle1', 'c', 'c');
insert into node (graph_id, id, name) values ('cycle1', 'd', 'd');

insert into edge (graph_id, from_id, to_id, cost) values ('cycle1', 'a', 'c', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('cycle1', 'b', 'a', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('cycle1', 'c', 'b', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('cycle1', 'd', 'c', 0);

-- cycle 2

insert into graph (id, name) values ('cycle2', 'graph');

insert into node (graph_id, id, name) values ('cycle2', 'a', 'a');
insert into node (graph_id, id, name) values ('cycle2', 'b', 'b');
insert into node (graph_id, id, name) values ('cycle2', 'c', 'c');

insert into edge (graph_id, from_id, to_id, cost) values ('cycle2', 'a', 'c', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('cycle2', 'b', 'a', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('cycle2', 'c', 'b', 0);

-- cycle 3 and disjoint

insert into graph (id, name) values ('cycle_disjoint', 'graph');

insert into node (graph_id, id, name) values ('cycle_disjoint', 'a', 'a');
insert into node (graph_id, id, name) values ('cycle_disjoint', 'b', 'b');
insert into node (graph_id, id, name) values ('cycle_disjoint', 'c', 'c');
insert into node (graph_id, id, name) values ('cycle_disjoint', 'd', 'd');
insert into node (graph_id, id, name) values ('cycle_disjoint', 'e', 'e');

insert into edge (graph_id, from_id, to_id, cost) values ('cycle_disjoint', 'a', 'c', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('cycle_disjoint', 'b', 'a', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('cycle_disjoint', 'c', 'b', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('cycle_disjoint', 'd', 'e', 0);

-- no cycle

insert into graph (id, name) values ('no_cycle', 'graph');

insert into node (graph_id, id, name) values ('no_cycle', 'a', 'a');
insert into node (graph_id, id, name) values ('no_cycle', 'b', 'b');
insert into node (graph_id, id, name) values ('no_cycle', 'c', 'c');

insert into edge (graph_id, from_id, to_id, cost) values ('no_cycle', 'a', 'c', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('no_cycle', 'b', 'a', 0);
insert into edge (graph_id, from_id, to_id, cost) values ('no_cycle', 'b', 'c', 0);

-- loop

insert into graph (id, name) values ('loop', 'graph');

insert into node (graph_id, id, name) values ('loop', 'a', 'a');

insert into edge (graph_id, from_id, to_id, cost) values ('loop', 'a', 'a', 0);

-- no_connections

insert into graph (id, name) values ('no_connections', 'graph');

insert into node (graph_id, id, name) values ('no_connections', 'a', 'a');

-- path

insert into graph (id, name) values ('path', 'graph');

insert into node (graph_id, id, name) values ('path', 'a', 'a');
insert into node (graph_id, id, name) values ('path', 'b', 'b');
insert into node (graph_id, id, name) values ('path', 'c', 'c');
insert into node (graph_id, id, name) values ('path', 'd', 'd');
insert into node (graph_id, id, name) values ('path', 'e', 'e');
insert into node (graph_id, id, name) values ('path', 'f', 'f');

insert into edge (graph_id, from_id, to_id, cost) values ('path', 'a', 'b', 2);
insert into edge (graph_id, from_id, to_id, cost) values ('path', 'a', 'c', 5);
insert into edge (graph_id, from_id, to_id, cost) values ('path', 'a', 'f', 6.5);
insert into edge (graph_id, from_id, to_id, cost) values ('path', 'b', 'd', 3);
insert into edge (graph_id, from_id, to_id, cost) values ('path', 'c', 'e', 3);
insert into edge (graph_id, from_id, to_id, cost) values ('path', 'c', 'd', 1);
insert into edge (graph_id, from_id, to_id, cost) values ('path', 'd', 'f', 2);
insert into edge (graph_id, from_id, to_id, cost) values ('path', 'e', 'f', 2);
insert into edge (graph_id, from_id, to_id, cost) values ('path', 'e', 'a', 1);
```

5. [x] CLI Program

The schema in the document seemed broken with `"queries": ["cheapest": {...}]`, so I assumed it was meant
`"queries": [{"cheapest": {...}}]`.

Since there was no explicit mention if the schema should be for a single graph or multiple graphs, I had to change
the input query adding `graph` to accomodate for the proposed schema above.

Here is an input example for the `path` graph of the previous section

```
{
    "queries": [{
        "paths": {
            "graph": "path",
            "start": "a",
            "end": "f"
        }
    }, {
        "cheapest": {
            "graph": "path",
            "start": "a",
            "end": "f"
        }
    }, {
        "paths": {
            "graph": "path",
            "start": "d",
            "end": "a"
        }
    }, {
        "cheapest": {
            "graph": "path",
            "start": "d",
            "end": "a"
        }
    }]
}
```

About the JSON library. I opted to keep the standard library as it is simple enough.
Of course, it comes with the price that I need to check the input and validate the fields.
But for this sort of thing I think it is way better than adding a new dependency.
