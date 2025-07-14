"""Creates a graph database with neo4j to store the design information
"""
import os 
import sys 
import csv
import time 
import tempfile
import subprocess
from neo4j import GraphDatabase

# Usage
URI = "bolt://localhost:7687"
REMOTE_URI=""
USER = "neo4j"
PASSWORD = "your_password"


class Neo4jConnection:
    
    def __init__(self):
        self.neo4j_container_name = 'neo4j-apoc'
        self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    def close(self):
        self.driver.close()

    def clear_database(self):
        with self.driver.session() as session:
            result = session.write_transaction(self._clear_db)
            print(f"Cleared {result} nodes and relationships")

    @staticmethod
    def _clear_db(tx):
        query = """
        CALL apoc.periodic.iterate(
        'MATCH (n) RETURN n',
        'DETACH DELETE n',
        {batchSize: 10000}
        )
        YIELD batches, total
        RETURN batches, total
        """
        result = tx.run(query)
        stats = result.single()
        total_deleted = stats["total"]
        
        return total_deleted

    def test_connection(self):
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                for record in result:
                    print(record)
            print("Connection successful!")
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            sys.exit(1)

            
    def load_nodes_and_relationships(self, stage, cells_file, pins_file, nets_file, segments_file, edges_file, designs_file, ioports_file):
        design_query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/{stage}/%s' AS row
        CALL {{
                WITH row
                CREATE (d:Design {{
                    name: row.name,
                    id: row.id,  
                    stage: row.stage,
                    die_area: toFloat(row.die_area),
                    xmin: toFloat(row.xmin),
                    ymin: toFloat(row.ymin),
                    xmax: toFloat(row.xmax),
                    ymax: toFloat(row.ymax)
                }})
        }} IN TRANSACTIONS OF 10000 ROWS;
        """
        
        design_constraint = """
        CREATE CONSTRAINT IF NOT EXISTS FOR (d:Design) 
        REQUIRE (d.id, d.stage) IS UNIQUE
        """
        
        ioport_query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/{stage}/%s' AS row
        CALL {{
            WITH row
            CREATE (d:Port {{
                id: row.id ,  
                port_name: row.port_name,
                net_name: row.net_name,
                direction: row.direction,
                signal_type: row.signal_type,
                width: toFloat(row.width),
                height: toFloat(row.height),
                layer: row.layer,
                x: toFloat(row.x),
                y: toFloat(row.y)
            }})
        }} IN TRANSACTIONS OF 10000 ROWS;
        """
         
        cells_query = f"""
       LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/{stage}/%s' AS row
       CALL {{
        WITH row
        CREATE (n:Cell {{
            id: row.id ,  
            cell_name: row.cell_name,
            instance_name: row.instance_name,
            cell_height: toFloat(row.cell_height),
            cell_width: toFloat(row.cell_width),
            orientation: row.orientation,
            area: toFloat(row.area),
            is_seq: row.is_seq = 'True',
            is_macro: row.is_macro = 'True',
            is_in_clk: row.is_in_clk = 'True',
            is_buf: row.is_buf = 'True',
            is_inv: row.is_inv = 'True',
            is_endcap: row.is_endcap = 'True',
            is_filler: row.is_filler = 'True',
            is_physical_only: row.is_physical_only = 'True',
            static_power: toFloat(row.static_power),
            dynamic_power: toFloat(row.dynamic_power),
            x0: toFloat(row.x0),
            y0: toFloat(row.y0),
            x1: toFloat(row.x1),
            y1: toFloat(row.y1)
        }})
        }} IN TRANSACTIONS OF 10000 ROWS;
        """

        pins_query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/{stage}/%s' AS row
        CALL {{
            WITH row
            CREATE (n:CellInternalPin {{
                id: row.id ,  
                pin_name: row.pin_name,
                pin_type: row.pin_type,
                net_name: row.net_name,
                instance_name: row.instance_name,
                direction: row.direction,
                is_endpoint: row.is_endpoint = 'true',
                num_reachable_endpoint: toInteger(row.num_reachable_endpoint),
                pin_transition: toFloat(row.pin_transition),
                pin_slack: toFloat(row.pin_slack),
                pin_rise_arr: toFloat(row.pin_rise_arr),
                pin_fall_arr: toFloat(row.pin_fall_arr),
                input_pin_capacitance: row.input_pin_capacitance,
                x: toFloat(row.x),
                y: toFloat(row.y)
            }})
        }} IN TRANSACTIONS OF 10000 ROWS;
        """

        nets_query = f"""
       LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/{stage}/%s' AS row
       CALL {{
        WITH row
        CREATE (n:Net {{
            id: row.id ,  
            net_name: row.net_name,
            signal_type: row.signal_type,
            net_cap: toFloat(row.net_cap),
            net_res: toFloat(row.net_res),
            net_coupling: toFloat(row.net_coupling),
            fanout: toInteger(row.fanout),
            routed_length: toFloat(row.routed_length),
            total_cap: toFloat(row.total_cap)
        }})
        }} IN TRANSACTIONS OF 10000 ROWS;
        """
        
        segment_query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/{stage}/%s' AS row
        CALL {{
            WITH row
            CREATE (n:Segment {{
                id: row.id,  
                layer: row.layer
            }})
        }} IN TRANSACTIONS OF 10000 ROWS;
        """
        
        self.create_constraints(constraints=[
            design_constraint
        ])
        
        self._load_csv_to_neo4j(designs_file, design_query)
        self._load_csv_to_neo4j(ioports_file, ioport_query)
        self._load_csv_to_neo4j(cells_file, cells_query)
        self._load_csv_to_neo4j(pins_file, pins_query)
        self._load_csv_to_neo4j(nets_file, nets_query)
        self._load_csv_to_neo4j(segments_file, segment_query)
        self._load_edges_with_cypher(stage, edges_file)


    def _load_csv_to_neo4j(self, file_path, create_query):
        with self.driver.session() as session:
            query = create_query % file_path
            session.run(query)

    def _load_edges_with_cypher(self, stage, file_path):
        self.check_mismatched_ids(stage, file_path)
        
        query = f"""
        CALL apoc.periodic.iterate(
        "LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/{stage}/%s' AS row RETURN row",
        "MATCH (source)
        WHERE source.id = row.source
        MATCH (target)
        WHERE target.id = row.target 
        WITH source, target, row,
            CASE 
                WHEN source:Design AND target:Port THEN 'HAS_PORT'
                WHEN source:Design AND target:Cell THEN 'CONTAINS_CELL'
                WHEN source:Design AND target:Net THEN 'CONTAINS_NET'
                WHEN source:CellInternalPin AND target:Cell THEN 'BELONGS_TO'
                WHEN source:Cell AND target:CellInternalPin THEN 'HAS_PIN'
                WHEN source:Cell AND target:Net THEN 'CONNECTS_TO'
                WHEN source:Net AND target:Cell THEN 'CONNECTS_TO'
                WHEN source:Cell AND target:Cell THEN 'DRIVES'
                WHEN source:CellInternalPin AND target:Net THEN 'DRIVES_NET'
                WHEN source:Net AND target:CellInternalPin THEN 'CONNECTS_TO'
                WHEN source:Port AND target:Net THEN 'DRIVES_NET'
                WHEN source:Net AND target:Port THEN 'CONNECTS_TO'
                WHEN source:Net AND target:Segment THEN 'ROUTED_ON'
                ELSE 'UNKNOWN'
            END AS relationshipType
        CALL apoc.create.relationship(source, relationshipType, row, target) YIELD rel
        RETURN count(*)",
        {{batchSize:50000, iterateList:true, parallel:true}}
        )
        """ % file_path

        
        # WHEN source:CellInternalPin AND target:CellInternalPin THEN 'PIN_CONNECTS_TO_PIN'
        # WHEN source:Cell AND target:Net THEN 'CELL_CONNECTS_TO_NET'

        with self.driver.session() as session:
            try:
                result = session.run(query)
                summary = result.consume()
                created = summary.counters.relationships_created
                print(f"Total relationships created: {created}")
                
                # Get counts for each relationship type
                type_counts = session.run("""
                MATCH ()-[r]->()
                WHERE type(r) IN ['HAS_PORT', 'CONTAINS_CELL', 'CONTAINS_NET', 'HAS_PIN', 'CONNECTS_TO', 'DRIVES', 'DRIVES_NET', 'HAS_PIN', 'HAS_PIN', 'ROUTED_ON']
                RETURN type(r) AS type, COUNT(*) AS count
                """)
                for record in type_counts:
                    print(f"{record['type']} relationships: {record['count']}")
            except Exception as e:
                print(f"Error during edge import: {e}")

        self.verify_edges()

    
    def bulk_import_nodes_and_relationships(self, stages):
        node_imports = []
        edge_imports = []
        
        for stage in stages: 
            node_imports.extend(
                [f"--nodes=/var/lib/neo4j/import/{stage}/designs.csv",
                f"--nodes=/var/lib/neo4j/import/{stage}/ioports.csv",
                f"--nodes=/var/lib/neo4j/import/{stage}/cells.csv",
                f"--nodes=/var/lib/neo4j/import/{stage}/pins.csv",
                f"--nodes=/var/lib/neo4j/import/{stage}/nets.csv",
                f"--nodes=/var/lib/neo4j/import/{stage}/segment.csv"]
            ) 
            edge_imports.extend(
                [f"--relationships=/var/lib/neo4j/import/{stage}/HAS_PORT.csv",
                f"--relationships=/var/lib/neo4j/import/{stage}/CONTAINS_CELL.csv",
                f"--relationships=/var/lib/neo4j/import/{stage}/CONTAINS_NET.csv",
                f"--relationships=/var/lib/neo4j/import/{stage}/HAS_PIN.csv",
                f"--relationships=/var/lib/neo4j/import/{stage}/DRIVES.csv",
                f"--relationships=/var/lib/neo4j/import/{stage}/CONNECTS_TO_PORT.csv",
                f"--relationships=/var/lib/neo4j/import/{stage}/ROUTED_ON.csv",
                f"--relationships=/var/lib/neo4j/import/{stage}/DRIVES_NET.csv",
                f"--relationships=/var/lib/neo4j/import/{stage}/CONNECTS_TO.csv",
                f"--relationships=/var/lib/neo4j/import/{stage}/BELONGS_TO.csv"
                ]
            )
        
        import_command = [
            "docker", "exec",
            # "--user", f"{user_id}:{group_id}",
            self.neo4j_container_name,
            "neo4j-admin", "import",
            "--database=sky130",
            "--delimiter=,",
            "--array-delimiter=;",
            "--skip-bad-relationships",
            "--skip-duplicate-nodes",
            "--ignore-extra-columns",
            "--force"
        ] + node_imports + edge_imports
                        
        try: 
            subprocess.run(import_command, check=True)
            print("Bulk import completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error during bulk import: {e}")
        
        self.convert_node_properties_to_float_and_bool()
        self.create_index()
    
    def create_index(self):
        index_commands = [
            "CREATE INDEX IF NOT EXISTS FOR (s:Segment) ON (s.layer);",
            "CREATE INDEX IF NOT EXISTS FOR (n:Net) ON (n.net_name);",
            "CREATE INDEX IF NOT EXISTS FOR (n:Net) ON (n.signal_type);",
            "CREATE INDEX IF NOT EXISTS FOR (n:Net) ON (n.fanout);",
            "CREATE INDEX IF NOT EXISTS FOR (n:Net) ON (n.routed_length);",
            "CREATE INDEX IF NOT EXISTS FOR (n:Net) ON (n.net_cap);",
            "CREATE INDEX IF NOT EXISTS FOR (n:Net) ON (n.net_res);",
            "CREATE INDEX IF NOT EXISTS FOR (n:Net) ON (n.total_cap);",
            "CREATE INDEX IF NOT EXISTS FOR (p:CellInternalPin) ON (p.pin_name);",
            "CREATE INDEX IF NOT EXISTS FOR (p:CellInternalPin) ON (p.instance_name);",
            "CREATE INDEX IF NOT EXISTS FOR (p:CellInternalPin) ON (p.direction);",
            "CREATE INDEX IF NOT EXISTS FOR (p:CellInternalPin) ON (p.x);",
            "CREATE INDEX IF NOT EXISTS FOR (p:CellInternalPin) ON (p.y);",
            "CREATE INDEX IF NOT EXISTS FOR (c:Cell) ON (c.cell_name);",
            "CREATE INDEX IF NOT EXISTS FOR (c:Cell) ON (c.instance_name);",
            "CREATE INDEX IF NOT EXISTS FOR (c:Cell) ON (c.x0);",
            "CREATE INDEX IF NOT EXISTS FOR (c:Cell) ON (c.y0);",
            "CREATE INDEX IF NOT EXISTS FOR (c:Cell) ON (c.x1);",
            "CREATE INDEX IF NOT EXISTS FOR (c:Cell) ON (c.y1);",
            "CREATE INDEX IF NOT EXISTS FOR (p:Port) ON (p.port_name);",
            "CREATE INDEX IF NOT EXISTS FOR (p:Port) ON (p.net_name);",
            "CREATE INDEX IF NOT EXISTS FOR (d:Design) ON (d.name);",
            "CREATE INDEX IF NOT EXISTS FOR (d:Design) ON (d.stage);"
        ]

        try:
            for command in index_commands:
                subprocess.run([
                    "docker", "exec", self.neo4j_container_name,
                    "cypher-shell", "-u", USER, "-p", PASSWORD,
                    "--format", "plain", command
                ], check=True)
            print("Indexes created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating indexes: {e}") 

    def convert_node_properties_to_float_and_bool(self):
        conversion_commands = [
            # Convert float properties for Design nodes
            """
            CALL apoc.periodic.iterate(
                'MATCH (d:Design) WHERE apoc.meta.type(d.die_area) = "STRING" OR apoc.meta.type(d.xmin) = "STRING" RETURN d',
                'SET d.die_area = apoc.convert.toFloat(d.die_area),
                    d.xmin = apoc.convert.toFloat(d.xmin),
                    d.ymin = apoc.convert.toFloat(d.ymin),
                    d.xmax = apoc.convert.toFloat(d.xmax),
                    d.ymax = apoc.convert.toFloat(d.ymax)',
                {batchSize:1000, iterateList:true}
            );
            """,
            
            """
            CALL apoc.periodic.iterate(
                'MATCH (p:Port) WHERE apoc.meta.type(p.width) = "STRING" OR apoc.meta.type(p.x) = "STRING" RETURN p',
                'SET p.width = apoc.convert.toFloat(p.width),
                    p.height = apoc.convert.toFloat(p.height),
                    p.x = apoc.convert.toFloat(p.x),
                    p.y = apoc.convert.toFloat(p.y)',
                {batchSize:1000, iterateList:true}
            );
            """,

            """
            CALL apoc.periodic.iterate(
                'MATCH (c:Cell) WHERE apoc.meta.type(c.cell_height) = "STRING" OR apoc.meta.type(c.area) = "STRING" OR apoc.meta.type(c.is_seq) = "STRING" RETURN c',
                'SET c.cell_height = apoc.convert.toFloat(c.cell_height),
                    c.cell_width = apoc.convert.toFloat(c.cell_width),
                    c.area = apoc.convert.toFloat(c.area),
                    c.static_power = apoc.convert.toFloat(c.static_power),
                    c.dynamic_power = apoc.convert.toFloat(c.dynamic_power),
                    c.x0 = apoc.convert.toFloat(c.x0),
                    c.y0 = apoc.convert.toFloat(c.y0),
                    c.x1 = apoc.convert.toFloat(c.x1),
                    c.y1 = apoc.convert.toFloat(c.y1),
                    c.is_seq = apoc.convert.toBoolean(c.is_seq),
                    c.is_macro = apoc.convert.toBoolean(c.is_macro),
                    c.is_in_clk = apoc.convert.toBoolean(c.is_in_clk),
                    c.is_buf = apoc.convert.toBoolean(c.is_buf),
                    c.is_inv = apoc.convert.toBoolean(c.is_inv),
                    c.is_endcap = apoc.convert.toBoolean(c.is_endcap),
                    c.is_filler = apoc.convert.toBoolean(c.is_filler),
                    c.is_physical_only = apoc.convert.toBoolean(c.is_physical_only)',
                {batchSize:1000, iterateList:true}
            );
            """,

            """
            CALL apoc.periodic.iterate(
                'MATCH (p:CellInternalPin) WHERE apoc.meta.type(p.pin_transition) = "STRING" OR apoc.meta.type(p.is_endpoint) = "STRING" RETURN p',
                'SET p.pin_transition = apoc.convert.toFloat(p.pin_transition),
                    p.pin_slack = apoc.convert.toFloat(p.pin_slack),
                    p.input_pin_capacitance = apoc.convert.toFloat(p.input_pin_capacitance),
                    p.pin_rise_arr = apoc.convert.toFloat(p.pin_rise_arr),
                    p.pin_fall_arr = apoc.convert.toFloat(p.pin_fall_arr),
                    p.x =  apoc.convert.toFloat(p.x),
                    p.y =  apoc.convert.toFloat(p.y),
                    p.is_endpoint = apoc.convert.toBoolean(p.is_endpoint)',
                {batchSize:1000, iterateList:true}
            );
            """,

            """
            CALL apoc.periodic.iterate(
                'MATCH (n:Net) WHERE apoc.meta.type(n.net_cap) = "STRING" OR apoc.meta.type(n.net_res) = "STRING" RETURN n',
                'SET n.net_cap = apoc.convert.toFloat(n.net_cap),
                    n.net_res = apoc.convert.toFloat(n.net_res),
                    n.net_coupling = apoc.convert.toFloat(n.net_coupling),
                    n.routed_length = apoc.convert.toFloat(n.routed_length),
                    n.fanout = apoc.convert.toFloat(n.fanout),
                    n.total_cap = apoc.convert.toFloat(n.total_cap)',
                {batchSize:1000, iterateList:true}
            );
        """]
        try:
            for command in conversion_commands:
                subprocess.run(["docker", "exec", self.neo4j_container_name, "cypher-shell", "-u", "neo4j", "-p", "your_password", "--format", "plain", command], check=True)
            print("Node property conversion to float and boolean completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error during APOC conversion: {e}")
                
            
    def _delete_database(self, db_name):
        delete_command = [
            "docker", "exec",
            self.neo4j_container_name,
            "neo4j-admin", "database", "drop", db_name, "--if-exists"
        ]
        try: 
            subprocess.run(delete_command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error deleting database: {db_name}")
        
    def verify_edges(self):
        with self.driver.session() as session:
            result = session.run("""
            MATCH ()-[r]->()
            WHERE type(r) IN ['HAS_PORT', 'CONTAINS_CELL', 'CONTAINS_NET', 'HAS_PIN', 'CONNECTS_TO', 'DRIVES']
            RETURN type(r) AS type, COUNT(r) as count
            """)
            for record in result:
                print(f"Total {record['type']} relationships in database: {record['count']}")

    def check_mismatched_ids(self, stage, file_path):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/{stage}/%s' AS row
        OPTIONAL MATCH (source)
        WHERE source.id = row.source OR source.name = row.source
        OPTIONAL MATCH (target)
        WHERE target.id = row.target OR target.name = row.target
        WITH row, source, target
        WHERE source IS NULL OR target IS NULL
        RETURN row.source, row.target, source IS NULL AS sourceMissing, target IS NULL AS targetMissing
        LIMIT 1
        """ % file_path

        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                print(f"Mismatched edge: source={record['row.source']} {'(missing)' if record['sourceMissing'] else ''}, "
                    f"target={record['row.target']} {'(missing)' if record['targetMissing'] else ''}")

    def create_constraints(self, constraints):
        with self.driver.session() as session:
            for constraint in constraints: 
                result = session.run(constraint)


def get_node_descr(selected_nodes=None):

    design_descr = """
# Node: Design
Defines the design node. It has the following attributes: 
- `name`: STRING, specifies design name. Value examples: ['spm', 'counter'].
- `id`: STRING, unique identifies for the design node. Value examples: ['spm', 'counter'].
- `die_area`: FLOAT, specifies the die area of the design. Value examples: [200.87, 345.89]
- `stage`: STRING, Specifies the current physical design stage of the design. Value examples: ['floorplan', 'placement', 'routing', 'cts'].
- `xmin`: FLOAT, specifies the minimum x-coordinate (left boundary) of the design. Value examples: [0.0, 10.5].
- `ymin`: FLOAT, specifies the minimum y-coordinate (bottom boundary) of the design. Value examples: [0.0, 20.5].
- `xmax`: FLOAT, specifies the maximum x-coordinate (right boundary) of the design. Value examples: [200.5, 300.7].
- `ymax`: FLOAT, specifies the maximum y-coordinate (top boundary) of the design. Value examples: [150.5, 400.75].

The `xmin`, `ymin`, `xmax`, and `ymax` attributes define the bounding box of the design, where:
- The bottom-left corner of the design is located at (`xmin`, `ymin`).
- The top-right corner is located at (`xmax`, `ymax`).
These coordinates help define the physical boundaries of the design on the die.
"""

    io_port_descr = """
# Node: Port
Defines input and output ports of the design. It has the following attributes: 
- `id`: STRING, unique identifier for the I/O port. Value examples: ['in1', 'out2'].
- `port_name`: STRING, name of the I/O pin. Value examples: ['clk', 'reset', 'data_in'].
- `net_name`: STRING, name of the net connected to the I/O port. Value examples: ['clk_net', 'reset_net'].
- `signal_type`: STRING, signal type of the I/O port. Value examples: ['POWER', 'GROUND', 'SIGNAL']
- `direction`: STRING, direction of the I/O port. Value examples: ['INPUT', 'OUTPUT', 'INOUT'].
- `width`: FLOAT, width of the I/O port. Value examples: [1.0, 2.0].
- `height`: FLOAT, height of the I/O port. Value examples: [1.0, 2.0].
- `layer`: STRING, metal layer on which the I/O port is drawn on. Value examples: ['met1', 'met2', 'met3', 'met4', 'met5'].
- `x`: FLOAT, the horizontal position of the I/O port on the design's layout grid. The value typically ranges from xmin to xmax, where xmin is the leftmost boundary of the design (often 0.0) and xmax is the rightmost boundary of the design. Value examples: [0.0, 100.5]
- `y`: FLOAT, the vertical position of the I/O port on the design's layout grid. The value typically ranges from ymin to ymax, where ymin is the bottommost boundary of the design (often 0.0) and ymax is the topmost boundary of the design. Value examples: [0.0, 200.75]
"""

    cell_descr = """
# Node: Cell
Defines cells in the design. It has the following attributes:
- `id`: STRING, unique identifier for the cell. Value examples: ['sky130_fd_sc_hd__buf_1', 'sky130_fd_sc_hd__xnor2_2'].
- `cell_name`: STRING, name of the cell, this name matches the name in the PDK. Value examples: ['sky130_fd_sc_hd__xnor2_2', 'sky130_fd_sc_hd__nand2_2'].
- `instance_name`: STRING, name of cell instance, this is a unique identifier for the cell. Value examples: ['_24_', '_32_'].
- `cell_height`: FLOAT, height of the cell. Value examples: [2720].
- `cell_width`: FLOAT, width of the cell. Value examples: [460].
- `orientation`: STRING, orientation of the cell. Value examples: ['N', 'FN', 'S'].
- `area`: FLOAT, area of the cell. Value examples: [0.4968, 1.9872].
- `is_seq`: BOOLEAN, indicates if the cell is a sequential cell (i.e flip-flop or latch cell). Value examples: [true, false].
- `is_macro`: BOOLEAN, indicates if the cell is a macro. Value examples: [true, false].
- `is_in_clk`: BOOLEAN, indicates if the cell is in the clock network. Value examples: [true, false].
- `is_buf`: BOOLEAN, indicates if the cell is a buffer. Value examples: [true, false].
- `is_inv`: BOOLEAN, indicates if the cell is an inverter. Value examples: [true, false].
- `is_endcap`: BOOLEAN, indicates if the cell is an endcap. Value examples: [true, false].
- `is_filler`: BOOLEAN, indicates if the cell is a filler. Value examples: [true, false].
- `is_physical_only`: BOOLEAN, indicates if the cell is a physical only cell. Value examples: [true, false].
- `static_power`: FLOAT, static power consumption of the cell. Value examples: [0.0001, 0.0005].
- `dynamic_power`: FLOAT, dynamic power consumption of the cell. Value examples: [0.001, 0.005].
- `x0`: FLOAT, x-coordinate of the lower-left corner. Value examples: [0.0, 10.5].
- `y0`: FLOAT, y-coordinate of the lower-left corner. Value examples: [0.0, 15.3].
- `x1`: FLOAT, x-coordinate of the upper-right corner. Value examples: [0.46, 11.42].
- `y1`: FLOAT, y-coordinate of the upper-right corner. Value examples: [1.08, 17.46].
"""

    pin_descr = """
# Node: CellInternalPin 
Defines cell internal pins. It has the following attributes: 
- `id`: STRING, Unique identifier for the cell pin.
- `pin_name`: STRING, Name of the cell pin.
- `direction`: STRING, Direction of the cell pin, whether it is an INPUT, OUTPUT, or INOUT pin. 
- `net_name`: STRING, Name of the net this cell pin is connected to.
- `instance_name`: STRING, Signal direction of the cell pin.
- `is_endpoint`: BOOLEAN, Indicates if this cell pin is an endpoint in timing analysis.
- `num_reachable_endpoint`: INTEGER, Number of endpoints reachable from this cell pin.
- `pin_transition`: FLOAT,  Transition time (slew) at this cell pin,
- `pin_slack`: FLOAT, Slack time at this cell pin,
- `pin_rise_arr`: FLOAT, Arrival time for rising transitions at this cell pin
- `pin_fall_arr`: FLOAT, Arrival time for falling transitions at this cell pin
- `input_pin_capacitance`: FLOAT, Input capacitance of the cell pin.
- `X`: FLOAT, X-coordinate of the pin's position .
- `Y`: FLOAT, Y-coordinate of the pin's position.
"""


    net_descr = """
# Node: Net
Defines nets in the design. It has the following attributes: 
- `id`: STRING, Unique identifier for the net.
- `net_name`: STRING, Name of the net.
- `signal_type`: STRING. Signal type of this net, whether it is a Power, Ground, CLOCK, or Signal net. Value examples: [`SIGNAL`, `POWER`, `GROUND`, `CLOCK`] 
- `net_cap`: FLOAT, Capacitance of the net.
- `net_res`: FLOAT, Resistance of the net.
- `net_coupling`: FLOAT, Coupling capacitance of the net with neighboring nets. 
- `fanout`: INTEGER, Number of sink pins connected to this net.
- `routed_length`: FLOAT, Total routed length of the net.
- `total_cap`: FLOAT, Total capacitance of the net, including pin and coupling capacitances. 
"""

    segment_descr = """
# Node: Segment
Defines wire segments (metal layers) used for routing the net node. 
- `id`: STRING, Unique identifier for the segment.
- `layer`: STRING, Name of the metal routing layer. Value Examples: ['met1', 'met2', 'met3']
"""
    descr_dict = {
        'Design': design_descr,
        'Port': io_port_descr,
        'Cell': cell_descr,
        'CellInternalPin': pin_descr,
        'Net': net_descr,
        'Segment': segment_descr

    }

    if not selected_nodes:
        selected_nodes = list(descr_dict.keys())
        
    descr = ""
    for node in selected_nodes: 
        descr += descr_dict[node]
    return descr 


def get_relationship_descr(selected_nodes=None):
    connected_to = """
Relationship: Various (as specified in the CASE statement)
`type`: STRING, Specifies the type of connection between nodes.
`target`: STRING, Identifier of the target node in the relationship.
`relationship`: STRING, Name of the relationship type.
`source`: STRING, Identifier of the source node in the relationship.
"""

    design_cell_conn = """(:Design)-[:CONTAINS_CELL]->(:Cell)\n"""
    design_net_conn = """(:Design)-[:CONTAINS_NET]->(:Net)\n"""
    design_ioport_conn = """(:Design)-[:HAS_PORT]->(:Port)\n"""
    cell_internal_pin_conn = """(:Cell)-[:HAS_PIN]->(:CellInternalPin)\n"""
    pin_cell_conn = """(:CellInternalPin)-[:BELONGS_TO]->(:Cell)\n"""
    cell_cell_conn = """(:Cell)-[:DRIVES]->(:Cell)\n"""
    cell_net_conn = """(:Cell)-[:CONNECTS_TO]->(:Net)\n"""
    net_segment_conn = """(:Net)-[:ROUTED_ON]->(:Segment)\n"""

    port_net_conn = """(:Port)-[:DRIVES_NET]->(:Net)\n"""
    net_port_conn = """(:Net)-[:CONNECTS_TO]->(:Port)\n"""  

    pin_net_conn = """(:CellInternalPin)-[:DRIVES_NET]->(:Net)\n"""  
    net_pin_conn = """(:Net)-[:CONNECTS_TO]->(:CellInternalPin)\n""" 

    valid_conn = """\n## Valid Connections:\n"""

    if not selected_nodes: 
        selected_nodes = ['Design', 'Port', 'Cell', 'CellInternalPin', 'Net', 'Segment']

    if set(['Design', 'Cells']).issubset(set(selected_nodes)):
        valid_conn += design_cell_conn 
    
    if set(['Design', 'Net']).issubset(set(selected_nodes)): 
        valid_conn += design_net_conn
    
    if set(['Design', 'Port']).issubset(set(selected_nodes)): 
        valid_conn += design_ioport_conn 
    
    if set(['Cell']).issubset(set(selected_nodes)): 
        valid_conn += cell_cell_conn 
    
    if set(['Cell', 'CellInternalPin']).issubset(set(selected_nodes)): 
        valid_conn += cell_internal_pin_conn 
        valid_conn += pin_cell_conn
    
    if set(['Cell', 'Net']).issubset(set(selected_nodes)): 
        valid_conn += cell_net_conn 
                
                
    if set(['CellInternalPin', 'Net']).issubset(set(selected_nodes)):
        valid_conn += pin_net_conn 
        valid_conn += net_pin_conn 
    
    if set(['Net', 'Port']).issubset(set(selected_nodes)):
        valid_conn += port_net_conn
        valid_conn += net_port_conn

    if set(['Net', 'Segment']).issubset(set(selected_nodes)):
        valid_conn += net_segment_conn
        
    descr = valid_conn

    return descr



def get_relationship_descr_verbose(selected_nodes=None):
    design_cell_conn = """
(:Design)-[:CONTAINS_CELL]->(:Cell)
This relationship links a design to its cells.
"""
    design_net_conn = """
(:Design)-[:CONTAINS_NET]->(:Net)
This relationship links a design to its nets.
"""
    design_ioport_conn = """
(:Design)-[:HAS_PORT]->(:Port)
This relationship links a design to its input/output ports.
"""
    cell_internal_pin_conn = """
(:Cell)-[:HAS_PIN]->(:CellInternalPin)
This relationship connects a cell to its internal input and output pins, which connect to other cells or nets. 
"""

    pin_cell_conn = """
(:CellInternalPin)-[:BELONGS_TO]->(:Cell)
This relationship indicates that a specific internal pin belongs to a particular cell.
"""

    cell_cell_conn = """
(:Cell)-[:DRIVES]->(:Cell)
This relationship shows that one cell is connected to (drives) another cell.
"""

    cell_net_conn = """
(:Cell)-[:CONNECTS_TO]->(:Net)
This relationship shows that cell is connected to a net node.

(:Net)-[:CONNECTS_TO]->(:Cell)
This relationship shows that a net is connected to a cell node.
"""

    net_segment_conn = """
(:Net)-[:ROUTED_ON]->(:Segment)
This relationship indicates that a net is routed on a specific segment (metal layer).
"""
 
    port_net_conn = """
Ports are connected to nets throught these two relationships: 
    - For input ports: 
    (:Port)-[:DRIVES_NET]->(:Net)
    This relationship signifies that an input port is driving a net.

    - for output ports: 
    (:Net)-[:CONNECTS_TO]->(:Port)
    This relationship indicates that a net is driving an output port. 
"""

    pin_net_conn = """
(:CellInternalPin)-[:DRIVES_NET]->(:Net)
This relationship indicates that an output cell pin drives a net. 
"""  
    net_pin_conn = """
(:Net)-[:CONNECTS_TO]->(:CellInternalPin)
This relationship indicates that a net is driving an input cell pin. 
""" 
   
    valid_conn = """\n## Valid Connections:\n"""

    if not selected_nodes: 
        selected_nodes = ['Design', 'Port', 'Cell', 'CellInternalPin', 'Net', 'Segment']

    if set(['Design', 'Cell']).issubset(set(selected_nodes)):
        valid_conn += design_cell_conn 
    
    if set(['Design', 'Net']).issubset(set(selected_nodes)): 
        valid_conn += design_net_conn
    
    if set(['Design', 'Port']).issubset(set(selected_nodes)): 
        valid_conn += design_ioport_conn 
    
    if set(['Cell']).issubset(set(selected_nodes)): 
        valid_conn += cell_cell_conn 
    
    if set(['Cell', 'CellInternalPin']).issubset(set(selected_nodes)): 
        valid_conn += cell_internal_pin_conn 
        valid_conn += pin_cell_conn
    
    if set(['Cell', 'Net']).issubset(set(selected_nodes)): 
        valid_conn += cell_net_conn 
        
    if set(['CellInternalPin', 'Net']).issubset(set(selected_nodes)):
        valid_conn += pin_net_conn 
        valid_conn += net_pin_conn 
    
    if set(['Net', 'Port']).issubset(set(selected_nodes)):
        valid_conn += port_net_conn

    if set(['Net', 'Segment']).issubset(set(selected_nodes)):
        valid_conn += net_segment_conn
        
    # if set(['pin']).issubset(set(selected_nodes)):
    #     valid_conn += pin_pin_conn 
    # if set(['cell', 'net']).issubset(set(selected_nodes)): 
    #     valid_conn += cell_net_conn 
    
    descr = valid_conn

    return descr

__all__ = [
    'URI',
    'USER',
    'PASSWORD',
    'Neo4jConnection'
]

def main():    
    neo4j = Neo4jConnection()
    
    neo4j.test_connection()
    neo4j.convert_node_properties_to_float_and_bool()

    


if __name__ == '__main__':
    main()