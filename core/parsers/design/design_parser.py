"""Parses design files (def, sdc, spef) into relational tables
"""
import os 
import gc
import sys 
import csv
import glob
import json
import argparse 
import odb 
import openroad 
import subprocess
import openroad as ord
import networkx as nx
from openroad import Tech, Design, Timing
from collections import defaultdict

from design_utils import Cell, Pin, Net, Pin_Num_Reachable_Endpoint, IOPort, DesignInfo, parse_cells, parse_pins, parse_ioports, parse_nets
from def2graph import create_graph 
from py2neo import Graph, Node, Relationship
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from core.database.graphdb import Neo4jConnection


def load_design(design_def, sdc_file, spef_file, liberty_files, tech_files, lef_files):
  tech = Tech()
  
  for liberty in liberty_files:  
    tech.readLiberty(liberty)
    
  for tech_file in tech_files:
    tech.readLef(tech_file)
  
  for lef in lef_files:
    tech.readLef(lef)
  
  design = Design(tech)
  design.readDef(design_def)

  output1 = design.evalTclString("read_sdc " + sdc_file)  
  if spef_file: 
    output2 = design.evalTclString("read_spef " + spef_file)
  output3 = design.evalTclString("set_propagated_clock [all_clocks]")

  return tech, design


def parse_design(stage, design_def, sdc_file, spef_file, liberty_files, tech_files, lef_files, output_dir):
  tech_design, design = load_design(
    design_def=design_def, 
    sdc_file=sdc_file, 
    spef_file=spef_file, 
    liberty_files=liberty_files, 
    tech_files=tech_files, 
    lef_files=lef_files
  )
  
  db = ord.get_db()
  chip = db.getChip()
  block = ord.get_db_block()
  tech = ord.get_db_tech()
  insts = block.getInsts()
  nets = block.getNets()
  
  die_area = block.getDieArea()
  
  db_units_per_micron = db.getTech().getDbUnitsPerMicron()
  xmin, ymin, xmax, ymax = die_area.xMin() / db_units_per_micron, \
    die_area.yMin() / db_units_per_micron, \
    die_area.xMax() / db_units_per_micron, \
    die_area.yMax() / db_units_per_micron

  area = ((xmax - xmin) * (ymax - ymin)) 

  print("NUMBER OF INSTANCES [" + str(len(insts)) + "]")
  print("NUMBER OF Nets [" + str(len(nets)) + "]")
  
  timing = Timing(design)
  design_name = block.getName()

  io_ports = parse_ioports(block=block)
  
  cell_list = parse_cells(
    design=design, 
    insts=insts,
    timing=timing
  )
  
  net_list = parse_nets(
    design=design, 
    nets=nets, 
    timing=timing
  )
  
  design_info = DesignInfo(
    stage=stage,
    name=design_name, 
    die_area=area, 
    rect=(xmin, ymin, xmax, ymax), 
    cells=cell_list, 
    nets=net_list, 
    io_ports=io_ports
  )

  return design_info
  
  
def create_graph(gates, nets, design_info):
  G = nx.DiGraph()
  G.add_node(
    design_info.name, 
    type='Design', 
    **design_info.to_dict()
  )

  input_ports = []
  output_ports = []
  inout_ports = []
  
  for port in design_info.io_ports: 
    G.add_node(
      f"IO:{port.port_name}", 
      type='Port', 
      **port.to_dict()
    )   
    G.add_edge(design_info.name, f"IO:{port.port_name}")  
    
    if port.direction == "OUTPUT":
      output_ports.append(port.port_name)
    if port.direction == "INPUT":
      input_ports.append(port.port_name)
    elif port.direction == 'INOUT':
      inout_ports.append(port.port_name)
  
  for gate in gates:
    G.add_node(
      gate.instance_name, 
      type='Cell', 
      **gate.to_dict()
    )   
    G.add_edge(design_info.name, gate.instance_name) 
    for pin in gate.pins:
      G.add_node(
        pin.pin_name, 
        type='CellInternalPin', 
        **pin.to_dict()
      )
      G.add_edge(gate.instance_name, pin.pin_name)
      G.add_edge(pin.pin_name, gate.instance_name)

  for net in nets:
    G.add_node(
      net.net_name, 
      type='Net', 
      **net.to_dict()
    )
    G.add_edge(design_info.name, net.net_name)  
    if net.net_name in input_ports: 
      G.add_edge(f"IO:{net.net_name}", net.net_name)
    if net.net_name in output_ports:
      G.add_edge(net.net_name, f"IO:{net.net_name}")    
    if net.net_name in inout_ports:
      G.add_edge(f"IO:{net.net_name}", net.net_name)

    for dst, dst_inst in zip(net.net_dsts, net.net_dst_instances): 
      G.add_edge(net.net_name, dst)
      G.add_edge(dst_inst, net.net_name)
      G.add_edge(net.net_name, dst_inst)

    for src, src_inst in zip(net.net_src, net.net_src_instance): 
      G.add_edge(src, net.net_name)
      G.add_edge(src_inst, net.net_name)
      G.add_edge(net.net_name, src_inst)

    if net.signal_type not in ['GROUND', 'POWER']: 
      for src_inst, src_pin in zip(net.net_src_instance, net.net_src):
        for dst_inst, dst_pin in zip(net.net_dst_instances, net.net_dsts):
          G.add_edge(src_inst, dst_inst)
          # G.add_edge(src_pin, dst_pin)

    for segment in net.segments: 
      G.add_node(segment.layer, type='Segment', layer=segment.layer)
      G.add_edge(net.net_name, segment.layer) #**segment.to_dict()
      
  return G



def export_nodes_to_csv(graph, stage, node_attributes, output_dir, bulk_format=False):
  cells_file_path = os.path.join(output_dir, f'cells.csv')
  pins_file_path = os.path.join(output_dir, f'pins.csv')
  nets_file_path = os.path.join(output_dir, f'nets.csv')
  design_file_path = os.path.join(output_dir, f'designs.csv')
  ioport_file_path = os.path.join(output_dir, f'ioports.csv')
  segment_file_path = os.path.join(output_dir, f'segment.csv')

  if bulk_format:
    id_key = ':ID'
    type_key = ':LABEL'
  else:
    id_key = 'id'
    type_key = 'type'
  
  id_type = [id_key, type_key] 
    
  # Open CSV files
  with open(cells_file_path, 'w', newline='') as cells_csvfile, \
    open(pins_file_path, 'w', newline='') as pins_csvfile, \
    open(nets_file_path, 'w', newline='') as nets_csvfile, \
    open(design_file_path, 'w', newline='') as design_csvfile, \
    open(ioport_file_path, 'w', newline='') as ioport_csvfile, \
    open(segment_file_path, 'w', newline='') as segment_csvfile:

    cells_writer = csv.DictWriter(cells_csvfile, fieldnames=id_type+node_attributes['Cell'])
    pins_writer = csv.DictWriter(pins_csvfile, fieldnames=id_type+node_attributes['CellInternalPin'])
    nets_writer = csv.DictWriter(nets_csvfile, fieldnames=id_type+node_attributes['Net'])
    design_writer = csv.DictWriter(design_csvfile, fieldnames=id_type+node_attributes['Design'])
    io_port_writer = csv.DictWriter(ioport_csvfile, fieldnames=id_type+node_attributes['Port'])
    segment_writer = csv.DictWriter(segment_csvfile, fieldnames=id_type+node_attributes['Segment'])
  
    cells_writer.writeheader()
    pins_writer.writeheader()
    nets_writer.writeheader()
    design_writer.writeheader()
    io_port_writer.writeheader()
    segment_writer.writeheader()
     
    for node, data in graph.nodes(data=True):
      row = {id_key: f"{node}_{stage}"}
      if bulk_format: 
        data[type_key] = data.pop("type")

      row.update(data)

      if type_key not in data:
        print(f"Skipping node {node} because it lacks a 'type' attribute.")
        continue         
      if data[type_key] == 'Cell':
        cells_writer.writerow(row)
      elif data[type_key] == 'CellInternalPin':
        pins_writer.writerow(row)
      elif data[type_key] == 'Net':
        nets_writer.writerow(row)
      elif data[type_key] == 'Design':
        design_writer.writerow(row)
      elif data[type_key] == 'Port':
        io_port_writer.writerow(row)
      elif data[type_key] == 'Segment':
        segment_writer.writerow(row)


def export_edges_to_csv(G, stage, output_dir, bulk_format=False):
  if bulk_format:
    type_key = ':LABEL'
  else:
    type_key = 'type'
  
  file_path = os.path.join(output_dir, f'edges.csv')
  with open(file_path, 'w', newline='') as csvfile:
    fieldnames = ['source', 'target', 'relationship']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for source, target, data in G.edges(data=True):
      source_type = G.nodes[source].get(type_key)
      target_type = G.nodes[target].get(type_key)
      relationship = determine_relationship(source_type, target_type)
      row = {'source': f"{source}_{stage}", 'target': f"{target}_{stage}", 'relationship': relationship}
      row.update(data)
      writer.writerow(row)

  writers_dict = {}
  relationships = ['HAS_PORT', 'CONTAINS_CELL', 'CONTAINS_NET', 'BELONGS_TO', 'HAS_PIN',  'CONNECTS_TO', 'DRIVES', 'ROUTED_ON', 'DRIVES_NET', 'CONNECTS_TO_PORT']
  
  for relationship in relationships:
    file_path = os.path.join(output_dir, f'{relationship}.csv')
    csvfile = open(file_path, 'w', newline='')
    writer = csv.DictWriter(csvfile, fieldnames=[':START_ID', ':END_ID', ':TYPE'])
    writer.writeheader()
    writers_dict[relationship] = (writer, csvfile)

  for source, target, data in G.edges(data=True):
    source_type = G.nodes[source].get(type_key)
    target_type = G.nodes[target].get(type_key)
   
    if target_type == 'CellInternalPin':
      direction = G.nodes[target].get('direction')
    else:
      direction = None 

    relationship = determine_relationship(source_type, target_type, direction)
   
    if relationship == 'UNKNOWN':
      continue 
    
    row = {':START_ID': f"{source}_{stage}", ':END_ID': f"{target}_{stage}", ':TYPE': relationship}
    row.update(data)
    
    if source == "NET" and target == "PORT": 
      writer, _ = writers_dict["CONNECTS_TO"]
    else:
      writer, _ = writers_dict[relationship]

    writer.writerow(row)

  for writer, csvfile in writers_dict.values():
    csvfile.close()


def determine_relationship(source_type, target_type, direction=None):
  if source_type == 'Design' and target_type == 'Port':
    return 'HAS_PORT'
  elif source_type == 'Design' and target_type == 'Cell':
    return 'CONTAINS_CELL'
  elif source_type == 'Design' and target_type == 'Net':
    return 'CONTAINS_NET'
  elif source_type == 'CellInternalPin' and target_type == 'Cell':
    return 'BELONGS_TO'
  elif source_type == 'Cell' and target_type == 'CellInternalPin':
    if direction == 'INPUT':
      return 'HAS_PIN'
    elif direction == 'OUTPUT': 
      return 'HAS_PIN'
    else:
      return 'HAS_PIN'
  elif source_type == 'Net' and target_type == 'CellInternalPin':
    return 'CONNECTS_TO'
  elif source_type == 'CellInternalPin' and target_type == 'CellInternalPin':
    return 'CONNECTS_TO'
  elif source_type == 'CellInternalPin' and target_type == 'Net':
    return 'DRIVES_NET'
  elif source_type == 'Cell' and target_type == 'Cell':
    return 'DRIVES'
  elif source_type == 'Cell' and target_type == 'Net':
    return 'CONNECTS_TO'
  elif source_type == 'Net' and target_type == 'Cell':
    return 'CONNECTS_TO'
  elif source_type == 'Net' and target_type == 'Port':
    return 'CONNECTS_TO'
  elif source_type == 'Port' and target_type == 'Net':
    return 'DRIVES_NET'
  elif source_type == 'Net' and target_type == 'Port':
    return 'CONNECTS_TO'
  elif source_type == 'Net' and target_type == 'Segment':
    return 'ROUTED_ON'
  else:
    return 'UNKNOWN'


def export_edges_bytype_to_csv(G, stage, output_dir):
  edges_by_type = defaultdict(list)

  for source, target, data in G.edges(data=True):
    source_type = G.nodes[source].get('type')
    target_type = G.nodes[target].get('type')
  
    relationship = determine_relationship(source_type, target_type)
    if relationship == 'HAS_PIN':
      pin_direction = G.nodes[target].get('direction') 
      if pin_direction == 'OUTPUT':
        relationship = 'HAS_OUTPUT_PIN'
      else:
        relationship = 'HAS_INPUT_PIN'
          
    edge_data = {'source': f"{source}_{stage}", 'target': f"{target}_{stage}", 'relationship': relationship}
    edge_data.update(data)
    edges_by_type[relationship].append(edge_data)

  for relationship, edges in edges_by_type.items():
    file_path = os.path.join(output_dir, f'edges_{stage}_{relationship}.csv')
    
    with open(file_path, 'w', newline='') as csvfile:
      if edges:  
        fieldnames = ['source', 'target'] + list(edges[0].keys() - {'source', 'target'})
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for edge in edges:
            writer.writerow(edge)
      else:
        writer = csv.writer(csvfile)
        writer.writerow(['source', 'target'])

  print(f"Exported {len(edges_by_type)} relationship types to CSV files in {output_dir}")
  
    

def main():
  parser = argparse.ArgumentParser(description="Parse design files and output JSON")
  parser.add_argument('--input', type=str, help='Path to design files', default='./designs/spm-small')
  parser.add_argument('--stage', type=str, help='Specify specific stage', default=None)
  parser.add_argument('--pdk', type=str, help='Path to PDK', default='/home/manar/.volare/sky130A/libs.ref')
  parser.add_argument('--format', type=str, help='Specifief csv format: load, bulk',  default='load')
  parser.add_argument("--output_dir", help="Output directory", default='./output')
  args = parser.parse_args()

  input_dir = args.input 
  stage = args.stage 
  pdk_path = args.pdk 
  bulk_format = True if args.format == 'bulk' else False
  output_dir = args.output_dir 

  os.makedirs(output_dir, exist_ok=True)
  
  # pdk views
  scl_variant = 'sky130_fd_sc_hd'
  lib_path = os.path.join(pdk_path, scl_variant, 'lib')
  techlef_path = os.path.join(pdk_path, scl_variant, 'techlef')
  lef_path = os.path.join(pdk_path, scl_variant, 'lef')

  liberty_files = [os.path.join(lib_path, file) for file in os.listdir(lib_path) if 'ccsnoise' not in file ]
  tech_files = [os.path.join(techlef_path, file) for file in os.listdir(techlef_path) if 'nom' in file]
  lef_files = [os.path.join(lef_path, file) for file in os.listdir(lef_path) ]

  stages = [stage] if stage else ['floorplan', 'placement', 'routing', 'cts']

  for stage in stages:

    def_file = glob.glob(os.path.join(input_dir, stage, '*.def'))[0]
    sdc_file = glob.glob(os.path.join(input_dir, stage, '*.sdc'))[0]
    spef_file = glob.glob(os.path.join(input_dir, stage, '*.spef'))

    spef_file = spef_file[0] if len(spef_file) > 0 else None 

    # Run parse_design
    design_info = parse_design(
      stage=stage,
      design_def=def_file,
      sdc_file=sdc_file,
      spef_file=spef_file,
      liberty_files=liberty_files,
      tech_files=tech_files,
      lef_files=lef_files,
      output_dir=output_dir
    )
    
    output_dir = output_dir 
    
    graph = create_graph(
      gates=design_info.cells, 
      nets=design_info.nets, 
      design_info=design_info
    )
    
    node_attributes = {}
    node_attributes['Design'] = design_info.get_attributes()
    node_attributes['Port'] = design_info.io_ports[0].get_attributes()
    node_attributes['Cell'] = design_info.cells[0].get_attributes()
    node_attributes['CellInternalPin'] = design_info.cells[0].pins[0].get_attributes()
    node_attributes['Net'] = design_info.nets[0].get_attributes()
    node_attributes['Segment'] = design_info.nets[0].segments[0].get_attributes()

    export_nodes_to_csv(graph, stage, node_attributes, output_dir, bulk_format=bulk_format)
    export_edges_to_csv(graph, stage, output_dir, bulk_format=bulk_format)
    
    design_dict = {
      'name': design_info.name,
      'die_area': design_info.die_area,
      'cells': [cell.__dict__ for cell in design_info.cells],
      'nets': [net.__dict__ for net in design_info.nets],
      'io_ports': [port.__dict__ for port in design_info.io_ports]
    }


    

if __name__ == "__main__":
  main()