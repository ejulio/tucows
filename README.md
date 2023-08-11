# Tucows test

## Tasks

1. [ ] Download the file
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
with recursive cte as (
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
		concat(cte.nodes, e.to_id, ',') as nodes,
		(case when cte.nodes like concat('%,', e.to_id, ',%') then 1 else 0 end) as has_cycle
	from
		cte
		join edge e on e.from_id = cte.to_id and e.graph_id = cte.graph_id
	where
		cte.has_cycle = 0
)
select exists(select 1 from cte where has_cycle = 1 limit 1) as has_cycle;
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
```

5. [ ] CLI Program