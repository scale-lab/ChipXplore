"""Utility function and classes for parsing design files
"""
import os
import tqdm
import concurrent.futures
from functools import partial
from tqdm.contrib.concurrent import thread_map

import odb
import openroad as ord 


class DesignInfo:
    
  def __init__(self, name, die_area, rect, cells, nets, io_ports, stage):
    self.name = name 
    self.stage = stage 
    self.die_area = die_area
    self.xmin = rect[0]
    self.ymin = rect[1]
    self.xmax = rect[2]
    self.ymax = rect[3]
    self.cells = cells 
    self.nets = nets 
    self.io_ports = io_ports 
    self.dict = {
      'name': self.name,
      'stage': self.stage,
      'die_area': self.die_area,
      'xmin': self.xmin, 
      'ymin': self.ymin,
      'xmax': self.xmax,
      'ymax': self.ymax,
      'num_cells': len(self.cells),
      'num_nets': len(self.nets),
      'num_ioports': len(self.io_ports)
    }
    
  def print(self):
    print(f"Design {self.name}, Stage: {self.stage}, Die Area: {self.die_area}, Number of Cells: {len(self.cells)}, Number of Nets: {len(self.nets)}")

  def to_dict(self):
    return self.dict

  def get_attributes(self):
    dict_keys = self.dict.keys()
    return list(dict_keys)


class IOPort:
  def __init__(self, port_name, direction, signal_type, net_name, x, y, width, height, layer):
    self.port_name = port_name
    self.direction = direction 
    self.signal_type = signal_type
    self.net_name = net_name
    self.x = x 
    self.y = y 
    self.width = width 
    self.height = height
    self.layer = layer 
    self.dict = {
      'port_name': self.port_name,
      'direction': self.direction,
      'signal_type': self.signal_type,
      'net_name': self.net_name,
      'x': self.x,
      'y': self.y,
      'width': self.width,
      'height': self.height,
      'layer': self.layer
    }
    
  def print(self):
    print(f"Pin: {self.pin_name}, Direction: {self.direction}, X: {self.x}, Y: {self.y}, Width: {self.width}, Height: {self.height}, Layer: {self.layer}") 
  
  def to_dict(self):
    return self.dict
  
  def get_attributes(self):
    dict_keys = self.dict.keys()
    return list(dict_keys)


class Cell:
  """Stores cell properties
  """
  def __init__(self, cell_name, cell_height, cell_width, instance_name, orientation, is_seq, is_macro, is_in_clk, is_buf, is_inv, is_endcap, is_filler, is_physical_only, static_power, dynamic_power, x0, y0, x1, y1):
    self.cell_name = cell_name  
    self.cell_height = cell_height
    self.cell_width = cell_width
    self.area = cell_width * cell_height 
    self.instance_name = instance_name
    self.orientation = orientation
    self.is_seq = is_seq 
    self.is_macro = is_macro 
    self.is_in_clk = is_in_clk 
    self.is_buf = is_buf 
    self.is_inv = is_inv 
    self.is_endcap = is_endcap 
    self.is_filler = is_filler
    self.is_physical_only = is_physical_only
    self.static_power = static_power 
    self.dynamic_power = dynamic_power
    self.x0 = x0 
    self.y0 = y0 
    self.x1 = x1 
    self.y1 = y1 
    self.pins = []
    self.dict = {
      'cell_name': self.cell_name,
      'cell_height': self.cell_height,
      'cell_width': self.cell_width, 
      'area': self.area,
      'instance_name': self.instance_name,
      'orientation': self.orientation,
      'is_seq': self.is_seq,
      'is_macro': self.is_macro,
      'is_in_clk': self.is_in_clk,
      'is_buf': self.is_buf,
      'is_inv': self.is_inv,
      'is_endcap': self.is_endcap, 
      'is_filler': self.is_filler,
      'is_physical_only': self.is_physical_only,
      'static_power': self.static_power,
      'dynamic_power': self.dynamic_power,
      'x0': self.x0,
      'y0': self.y0,
      'x1': self.x1,
      'y1': self.y1
    }
    
  def add_pin(self, pin):
    self.pins.append(pin)

  def add_pins(self, pin_list):
    self.pins = pin_list
      
  def print(self):
    print(f"Cell Name: {self.cell_name}, Instance Name: {self.instance_name}, Static Power: {self.static_power}, Dynamic Power: {self.dynamic_power}, Number of Pins: {len(self.pins)}\n")
    print(f"Sequential? {self.is_seq},  Macro ? {self.is_macro}, In Clock ? {self.is_in_clk}, Buffer {self.is_buf}, Inverter? {self.is_inv}\n")

  def to_dict(self):
    return self.dict
 
  def get_attributes(self):
    dict_keys = self.dict.keys()
    return list(dict_keys)

class Pin:
    
  def __init__(self, pin_name, pin_type, net_name, is_in_clk, instance_name, direction, is_endpoint, num_reachable_endpoint, pin_transition, pin_slack, pin_rise_arr, pin_fall_arr, input_pin_capacitance, x, y):
    self.pin_name = pin_name
    self.pin_type = pin_type
    self.net_name = net_name 
    self.is_in_clk = is_in_clk
    self.instance_name = instance_name 
    self.direction = direction 
    self.is_endpoint = is_endpoint 
    self.num_reachable_endpoint = num_reachable_endpoint
    self.pin_transition = pin_transition 
    self.pin_slack = pin_slack 
    self.pin_rise_arr = pin_rise_arr 
    self.pin_fall_arr = pin_fall_arr 
    self.input_pin_capacitance = input_pin_capacitance
    self.x = x 
    self.y = y 
    self.dict = {
      # 'pin_name': self.pin_name,
      'net_name': self.net_name,
      'pin_type': self.pin_type,
      'is_in_clk': self.is_in_clk,
      'instance_name': self.instance_name,
      'direction': self.direction,
      'is_endpoint': self.is_endpoint,
      'num_reachable_endpoint': self.num_reachable_endpoint,
      'pin_transition': self.pin_transition,
      'pin_slack': self.pin_slack,
      'pin_rise_arr': self.pin_rise_arr,
      'pin_fall_arr': self.pin_fall_arr,
      'input_pin_capacitance': self.input_pin_capacitance,
      'x': self.x,
      'y': self.y
    }
 
  def to_dict(self):
    return self.dict 
  
  def print(self):
    print(f"Pin Name: {self.pin_name}, Net Name: {self.net_name}, Direction: {self.direction}, Capacitance: {self.input_pin_capacitance}, Num Reachable Endpoints: {self.num_reachable_endpoint}, X: {self.x}, Y: {self.y}")
    print(f"Pin Transition: {self.pin_transition}, Pin Slack: {self.pin_slack}, Rise Arrival: {self.pin_rise_arr}, Fall Arrival: {self.pin_fall_arr}")

  def get_attributes(self):
    dict_keys = self.dict.keys()
    return list(dict_keys)


class Net:
  """Store Net Properties
  """
  def __init__(self, net_name, signal_type, net_cap, net_res, net_coupling, fanout, routed_length, total_cap, net_src, net_dsts, net_src_instance, net_dst_instances, layers, segments):
    self.net_name = net_name
    self.signal_type = signal_type
    self.net_cap = net_cap 
    self.net_res = net_res 
    self.net_coupling = net_coupling
    self.fanout = fanout 
    self.routed_length = routed_length 
    self.total_cap = total_cap  
    self.net_src = net_src 
    self.net_dsts = net_dsts 
    self.net_src_instance = net_src_instance
    self.net_dst_instances = net_dst_instances
    self.layers = layers 
    self.segments = segments
    self.dict = {
      'net_name': self.net_name,
      'signal_type': self.signal_type,
      'net_cap': self.net_cap,
      'net_res': self.net_res,
      'net_coupling': self.net_coupling,
      'fanout': self.fanout,
      'routed_length': self.routed_length,
      'total_cap': self.total_cap,
      'net_src': self.net_src,
      'net_dsts': self.net_dsts,
      'net_src_instance': self.net_src_instance,
      'net_dst_instances': self.net_dst_instances,
      'layers': self.layers
    }
    
    
  def print(self):
    print(f"Net Name: {self.net_name}, Net Capacitance: {self.net_cap}, \
      Resistance: {self.net_res}, Coupling: {self.net_coupling}, Fanout: {self.fanout}, \
      Routed Length: {self.routed_length}, Total Capacitance: {self.total_cap}, Layers: {self.layers}") 

  def to_dict(self):
    return self.dict 

  def get_attributes(self):
    dict_keys = self.dict.keys()
    return list(dict_keys)

class Segment:
  
  def __init__(self, net_name, layer, x1='', y1='', x2='', y2=''):
    self.net_name = net_name 
    self.layer = layer 
    self.x1 = x1
    self.y1 = y1
    self.x2 = x2
    self.y2 = y2
    self.dict = {
      # 'x1': self.x1,
      # 'y1': self.y1, 
      # 'x2': self.x2, 
      # 'y2': self.y2,
      'layer': self.layer  
    } 
  
  def to_dict(self):
    return self.dict 

  def get_attributes(self):
    dict_keys = self.dict.keys()
    return list(dict_keys)


def is_physical_only_cell(cell):
  master = cell.getMaster()
  if master.getMTermCount() == 0:
    return True
  
  has_only_physical_pins = True
  for mterm in master.getMTerms():
    if mterm.getSigType() == 'SIGNAL':
      has_only_physical_pins = False
      break
  
  if has_only_physical_pins:
    return True
  
  return False
  

def parse_cell(design, timing, corner, db_units_per_micron, inst):
    # parse cell properties
    instance_name = inst.getName()
    BBox = inst.getBBox()
    x0, y0 = BBox.xMin() / db_units_per_micron, BBox.yMin() / db_units_per_micron
    x1, y1 = BBox.xMax() / db_units_per_micron, BBox.yMax() / db_units_per_micron

    master_cell = inst.getMaster()
    master_name = master_cell.getName()
    is_macro = master_cell.isBlock() 
    is_buf = design.isBuffer(master_cell) 
    is_inv = design.isInverter(master_cell) 
    is_in_clk = design.isInClock(inst) 
    
    def convert_power_to_nW(power_in_watts):
      return power_in_watts * 1e9
  
    cell_static_power = convert_power_to_nW(timing.staticPower(inst, corner))
    cell_dynamic_power = timing.dynamicPower(inst, corner)
    is_filler = master_cell.isFiller()
    is_endcap = master_cell.isEndCap()
    is_physical_only = is_physical_only_cell(inst)
    is_sequential = master_cell.isSequential()    
    cell_height = master_cell.getHeight() / db_units_per_micron
    cell_width = master_cell.getWidth() / db_units_per_micron
    cell_site = master_cell.getSite()
    
    cell_symmetry_r90 = cell_site.getSymmetryR90()
    cell_symmetry_x = cell_site.getSymmetryX()
    cell_symmetry_y = cell_site.getSymmetryY()
    orientation = inst.getOrient()
    
    cell = Cell(
      cell_name=master_name, 
      cell_height=cell_height,
      cell_width=cell_width,
      instance_name=instance_name, 
      orientation=orientation,
      is_seq=is_sequential, 
      is_macro=is_macro, 
      is_in_clk=is_in_clk, 
      is_buf=is_buf, 
      is_inv=is_inv, 
      is_endcap=is_endcap,
      is_filler=is_filler,
      is_physical_only=is_physical_only,
      static_power=cell_static_power, 
      dynamic_power=cell_dynamic_power, 
      x0=x0, 
      y0=y0,
      x1=x1,
      y1=y1
    )

    # parse pin properties 
    inst_ITerms = inst.getITerms()
    pins = parse_pins(design, inst_ITerms, timing, corner)
    cell.add_pins(pins)
    
    return cell


def parse_cells(design, insts, timing, parallel=False):
  corner = timing.getCorners()[0]
  
  db = ord.get_db()
  db_units_per_micron = db.getTech().getDbUnitsPerMicron()

  if parallel: 
    parse_cell_partial = partial(parse_cell, design, timing, corner, db_units_per_micron)
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
      cell_list = list(tqdm.tqdm(executor.map(parse_cell_partial, insts), total=len(insts)))
  else: 
    cell_list = [parse_cell(design, timing, corner, db_units_per_micron, inst) for inst in tqdm.tqdm(insts)]
    
  return cell_list


def parse_ioports(block):
  io_ports = []
  
  db = ord.get_db()
  db_units_per_micron = db.getTech().getDbUnitsPerMicron()

  for term in tqdm.tqdm(block.getBTerms()):
    pin_name = term.getName()
    bpin = term.getBPins()[0]
    boxes = bpin.getBoxes()
    direction = term.getIoType()
    sig_type = term.getSigType()

    net = term.getNet()
    net_name = net.getName() if net else None
      
    if boxes:
      box = boxes[0]  # Get the first box
      x = box.xMin() / db_units_per_micron
      y = box.yMin() / db_units_per_micron
      width = box.getDX() / db_units_per_micron
      height = box.getDY() / db_units_per_micron
      layer = box.getTechLayer().getName()

    port = IOPort(
      port_name=pin_name,
      net_name=net_name, 
      direction=direction,
      signal_type=sig_type,
      x=x,
      y=y,
      width=width,
      height=height,
      layer=layer
    )

    io_ports.append(port)

  return io_ports


def parse_segments(net):
  
  db = ord.get_db()
  dbunits = db.getTech().getDbUnitsPerMicron()

  segments = []
  total_wire_length = 0
  if net.isSpecial():
    wires = net.getSWires()
    for swire in wires:
      for box in swire.getWires():
        layer = box.getTechLayer()
        if layer: 
          segment = Segment(
            net_name=net.getName(),
            layer=layer.getName(),
          )
          segments.append(segment)
  else: 
    wire = net.getWire()
    if wire:
      wire_length = wire.length()
      length_microns = float(wire_length) / float(dbunits)
      total_wire_length += wire_length
      decoder = odb.dbWireDecoder()
      decoder.begin(wire)
      
      while True:
        current_opcode = decoder.peek()
        if current_opcode == odb.dbWireDecoder.END_DECODE:
          break
          
        wire_type = decoder.getWireType()
        if current_opcode in [odb.dbWireDecoder.PATH, odb.dbWireDecoder.SHORT, odb.dbWireDecoder.VWIRE]:
          layer = decoder.getLayer()
          if layer:
            x1, y1 = decoder.getPoint()
            segment = Segment(
              net_name=net.getName(),
              layer=layer.getName(),
              x1=x1,
              y1=y1
            )
            segments.append(segment)
            print(f"Segment on Layer: {layer.getName()} from ({x1}, {y1}) ")
        elif current_opcode == odb.dbWireDecoder.VIA:
            via = decoder.getVia()
            if via:
              bottom_layer = via.getBottomLayer()
              top_layer = via.getTopLayer()
              if bottom_layer and top_layer:
                layers.add(bottom_layer.getName())
                layers.add(top_layer.getName())
            #         x, y = decoder.getPoint()
                print(f" Via Segment from Layer: {bottom_layer.getName()} to Layer: {top_layer.getName()} at ({x}, {y})")
        elif current_opcode == odb.dbWireDecoder.TECH_VIA:
            tech_via = decoder.getTechVia()
            # if tech_via:
            #   via_name = tech_via.getName()
              # print(f"Tech Via Segment {via_name}")
              # bottom_layer = tech_via.getBottomLayer()
              # top_layer = tech_via.getTopLayer()
              # if bottom_layer :
              #     layers.add(bottom_layer.getName())
              #     # layers.add(top_layer.getName())
              #     x, y = decoder.getPoint()
              #     print(f"  Tech Via Segment from Layer: {bottom_layer.getName()}  ({x}, {y})")
        elif current_opcode == odb.dbWireDecoder.JUNCTION:
          print("Found Junction")
        elif current_opcode ==  odb.dbWireDecoder.POINT:
          point = decoder.getPoint()
          print("Found Point ", point)
        elif current_opcode == odb.dbWireDecoder.POINT_EXT:
          point = decoder.getPoint()
          print("Found Point EXT: ", point)
        else:
          print(f" Unsupported segment type: {current_opcode}")

        decoder.next()  # Move to the next segment

  return segments



def parse_single_net(design, timing, corner, dbunits, net):
  net_name = net.getName()
  net_cap = net.getTotalCapacitance()
  net_res = net.getTotalResistance()
  net_coupling = net.getTotalCouplingCap()
  total_cap = timing.getNetCap(net, corner, timing.Max)

  input_pins = []
  output_pins = []
  input_instances = []
  output_instances = []
    
  for ITerm in net.getITerms():
    ITerm_name = design.getITermName(ITerm)
    instance_name = ITerm.getInst().getName()
    if ITerm.isInputSignal():
      output_pins.append(ITerm_name)
      output_instances.append(instance_name)
    elif ITerm.isOutputSignal():
      input_instances.append(instance_name)
      input_pins.append(ITerm_name)
    else: # inout signals; probably power/gnd
      input_pins.append(ITerm_name)
      input_instances.append(instance_name)
      output_pins.append(ITerm_name)
      output_instances.append(instance_name)
      
  fanout = len(output_pins)
  routed_length = design.getNetRoutedLength(net) / dbunits
  
  segments = parse_segments(net)
  layers = set(segment.layer for segment in segments if hasattr(segment, 'layer'))
          
  return Net(
    net_name=net_name, 
    signal_type=net.getSigType(),
    net_cap=net_cap, 
    net_res=net_res, 
    net_coupling=net_coupling, 
    fanout=fanout, 
    routed_length=routed_length, 
    total_cap=total_cap,
    net_src=input_pins,
    net_dsts=output_pins,
    net_src_instance=input_instances,
    net_dst_instances=output_instances,
    layers=list(layers),
    segments=segments
  )


def parse_nets(design, nets, timing, parallel=False):
  corner = timing.getCorners()[0]
  
  db = ord.get_db()
  dbunits = db.getTech().getDbUnitsPerMicron()

  if parallel: 
    parse_net_partial = partial(parse_single_net, design, timing, corner, dbunits)    
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
      net_list = list(tqdm.tqdm(executor.map(parse_net_partial, nets), total=len(nets), desc="Parsing nets"))
  else:
    net_list = [parse_single_net(design, timing, corner, dbunits, net) for net in tqdm.tqdm(nets)]
    
  return net_list
  

def parse_pins(design, inst_ITerms, timing, corner):
  
  pin_list = []
  
  for ITerm in inst_ITerms:
    if ITerm.getNet(): 
      pin_type = ITerm.getNet().getSigType()
    else:
      pin_type = None 
    
    pin_name = design.getITermName(ITerm)
    pin_net_name = ITerm.getNet().getName() if  ITerm.getNet() else None 
    pin_is_in_clk = 1 if design.isInClock(ITerm.getInst()) else 0
    direction = 'OUTPUT' if ITerm.isOutputSignal() else 'INPUT'
    pin_instance_name = ITerm.getInst().getName()
    
    is_endpoint = timing.isEndpoint(ITerm)
    num_reachable_endpoint = Pin_Num_Reachable_Endpoint(ITerm, timing)
    pin_transition = timing.getPinSlew(ITerm)
    pin_slack = min(timing.getPinSlack(ITerm, timing.Fall, timing.Max), timing.getPinSlack(ITerm, timing.Rise, timing.Max))
    pin_rise_arr = timing.getPinArrival(ITerm, timing.Rise)
    pin_fall_arr = timing.getPinArrival(ITerm, timing.Fall)
    
    PinXY_list = ITerm.getAvgXY()  
    x, y = None, None     
    if PinXY_list[0]:
      x = PinXY_list[1]
      y = PinXY_list[2]
    
    input_pin_capacitance = None
    if ITerm.isInputSignal():
      input_pin_capacitance = timing.getPortCap(ITerm, corner, timing.Max)
      
    pin = Pin(
      pin_name=pin_name,
      net_name=pin_net_name,
      is_in_clk=pin_is_in_clk, 
      instance_name=pin_instance_name, 
      direction=direction, 
      is_endpoint=is_endpoint, 
      num_reachable_endpoint=num_reachable_endpoint, 
      pin_transition=pin_transition, 
      pin_slack=pin_slack,
      pin_rise_arr=pin_rise_arr,
      pin_fall_arr=pin_fall_arr, 
      input_pin_capacitance=input_pin_capacitance,
      x=x,
      y=y,
      pin_type=pin_type
    ) 

    pin_list.append(pin)
  
  return pin_list 

# def parse_pins(design, inst_ITerms, timing, corner, parallel_threshold=1, parallel=False):
#   parse_pin_partial = partial(parse_single_pin, design, timing, corner)
#   max_workers = min(32, os.cpu_count() + 4)  
#   if parallel: 
#     with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
#       pin_list = list(tqdm.tqdm(executor.map(parse_pin_partial, inst_ITerms), total=len(inst_ITerms)))
#   else:
#     pin_list = [parse_single_pin(design, timing, corner, ITerm) for ITerm in inst_ITerms]
  
#   return pin_list  


def Pin_Num_Reachable_Endpoint(ITerm, timing):
  tmp_net = ITerm.getNet()
  if not tmp_net: 
    return 0 
  tmp_ITerms = tmp_net.getITerms()
  num = 0
  for tmp_ITerm in tmp_ITerms:
    if timing.isEndpoint(tmp_ITerm):
      num += 1
  return num