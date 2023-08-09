from tucows.graph import parse, InvalidGraph
import pytest


def test_parse_valid_graph():
    g = parse("""<graph>
    <id>g0</id>
    <name>The Graph Name</name>
    <nodes>
        <node>
            <id>a</id>
            <name>A name</name>
        </node>
        <node>
            <id>e</id>
            <name>E name</name>
        </node>
    </nodes>
    <edges>
        <edge>
            <id>e1</id>
            <from>a</from>
            <to>e</to>
            <cost>42.789</cost>
        </edge>
        <edge>
            <id>e2</id>
            <from>a</from>
            <to>a</to>
        </edge>
    </edges>
</graph>""")

    assert g.id == "g0"
    assert g.name == "The Graph Name"
    assert len(g.nodes) == 2
    assert g.nodes[0].id == "a"
    assert g.nodes[0].name == "A name"
    assert g.nodes[1].id == "e"
    assert len(g.edges) == 2
    assert g.edges[0].id == "e1"
    assert g.edges[0].from_node == g.nodes[0]
    assert g.edges[0].to_node == g.nodes[1]
    assert g.edges[0].cost == 42.789
    assert g.edges[1].id == "e2"
    assert g.edges[1].cost == 0


def test_parse_no_edges():
    g = parse("""<graph>
    <id>g0</id>
    <name>The Graph Name</name>
    <nodes>
        <node>
            <id>a</id>
            <name>A name</name>
        </node>
    </nodes>
    <edges>
    </edges>
</graph>""")

    assert len(g.nodes) == 1
    assert len(g.edges) == 0

def test_parse_mising_nodes():
    with pytest.raises(InvalidGraph):
        parse("""<graph>
    <id>g0</id>
    <name>The Graph Name</name>
    <edges>
        <edge>
            <id>e1</id>
            <from>a</from>
            <to>e</to>
            <cost>42</cost>
        </edge>
        <edge>
            <id>e2</id>
            <from>a</from>
            <to>a</to>
        </edge>
    </edges>
</graph>""")

def test_parse_mising_edges():
    with pytest.raises(InvalidGraph):
        parse("""<graph>
    <id>g0</id>
    <name>The Graph Name</name>
    <nodes>
        <node>
            <id>a</id>
            <name>A name</name>
        </node>
        <node>
            <id>e</id>
            <name>E name</name>
        </node>
    </nodes>
</graph>""")

def test_parse_nodes_edges_out_of_order():
    with pytest.raises(InvalidGraph):
        parse("""<graph>
    <id>g0</id>
    <name>The Graph Name</name>
    <edges>
        <edge>
            <id>e1</id>
            <from>a</from>
            <to>e</to>
            <cost>42</cost>
        </edge>
        <edge>
            <id>e2</id>
            <from>a</from>
            <to>a</to>
        </edge>
    </edges>
    <nodes>
        <node>
            <id>a</id>
            <name>A name</name>
        </node>
        <node>
            <id>e</id>
            <name>E name</name>
        </node>
    </nodes>
</graph>""")

def test_parse_min_nodes():
    with pytest.raises(InvalidGraph):
        parse("""<graph>
    <id>g0</id>
    <name>The Graph Name</name>
    <nodes>
    </nodes>
    <edges>
        <edge>
            <id>e1</id>
            <from>a</from>
            <to>e</to>
            <cost>42</cost>
        </edge>
        <edge>
            <id>e2</id>
            <from>a</from>
            <to>a</to>
        </edge>
    </edges>
</graph>""")

def test_parse_duplicate_node_id():
    with pytest.raises(InvalidGraph):
        parse("""<graph>
        <id>g0</id>
        <name>The Graph Name</name>
        <nodes>
            <node>
                <id>duplicate id</id>
                <name>A name</name>
            </node>
            <node>
                <id>duplicate id</id>
                <name>E name</name>
            </node>
        </nodes>
        <edges>
        </edges>
    </graph>""")
