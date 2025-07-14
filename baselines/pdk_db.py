"""Benchmark query execution time against database size. 
"""

import re 
import os 
import glob 
import tqdm
import time 
import sqlite3
import argparse 

import matplotlib.pyplot as plt
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

from core.eval.metrics import execute_query
from core.utils import get_logger


test_queries_sky130 = [
    "SELECT Size_Height FROM Macros WHERE Name = 'sky130_fd_sc_hdll__a2bb2o_1'",
    "SELECT Size_Width FROM Macros WHERE Name = 'sky130_fd_sc_hdll__a2bb2o_1'",
    "SELECT Size_Height FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hdll' LIMIT 1",
    "SELECT Name FROM Macros  WHERE Cell_Library = 'sky130_fd_sc_hdll' ORDER BY Size_Width DESC LIMIT 1",
    "SELECT Name FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hdll' ORDER BY Size_Width LIMIT 1",
    "SELECT Cell_Library, AVG(Size_Width) AS Average_Width FROM Macros GROUP BY Cell_Library",
    "SELECT Antenna_Gate_Area FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hdll__a2bb2o_1') AND Direction = 'INPUT'",
    "SELECT Antenna_Diff_Area  FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hdll__a2bb2o_1') AND Direction = 'OUTPUT'",
    "SELECT Name FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hdll__nand2_1' AND Cell_Library = 'sky130_fd_sc_hdll') AND (Use = 'POWER' OR Use = 'GROUND')",
    "SELECT Macros.Name AS Cell_Name, SUM(Pins.Antenna_Gate_Area) AS Total_Antenna_Gate_Area FROM Pins JOIN Pin_Ports ON Pins.Pin_ID = Pin_Ports.Pin_ID JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = 'sky130_fd_sc_hdll' GROUP BY Macros.Name ORDER BY Total_Antenna_Gate_Area DESC LIMIT 1",
    "SELECT pp.Layer FROM Pins p JOIN Pin_Ports pp ON p.Pin_ID = pp.Pin_ID WHERE p.Name = 'A1_N' AND p.Direction = 'INPUT' AND p.Macro_ID IN (SELECT m.Macro_ID FROM Macros m WHERE m.Cell_Library ='sky130_fd_sc_hdll' and m.Name='sky130_fd_sc_hdll__a2bb2o_1');",
    "SELECT Layer FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hdll__nand3b_1' AND Cell_Library = 'sky130_fd_sc_hdll') AND Use IN ('POWER', 'GROUND'))",
    "SELECT Name, Size_Width, Size_Height, (Size_Width * Size_Height) AS Total_Area FROM Macros WHERE Macro_ID = ( SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Macro_ID IN (SELECT Macro_ID FROM Pins WHERE Use = 'SIGNAL') ORDER BY (Size_Width * Size_Height) DESC LIMIT 1 )",
    "SELECT DISTINCT Layer FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Use = 'SIGNAL' AND Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hdll'))",
    "SELECT Layer, COUNT(Pin_ID) AS Input_Pin_Count FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Direction = 'INPUT' AND Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hdll')) GROUP BY Layer",
    "SELECT DISTINCT m.Name AS Macro_Name FROM Macros m JOIN Pins p ON m.Macro_ID = p.Macro_ID JOIN Pin_Ports pp ON p.Pin_ID = pp.Pin_ID WHERE pp.Layer = 'met5' ORDER BY m.Name;",
    "SELECT Rect_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2 FROM Pin_Port_Rectangles WHERE Port_ID = (SELECT Port_ID FROM Pin_Ports WHERE Pin_ID = (SELECT Pin_ID FROM Pins WHERE Name = 'A' AND Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hdll__xnor3_2')))",
    "SELECT Macros.Name FROM Macros JOIN ( SELECT Pins.Macro_ID, AVG(Rect_Count) AS Avg_Rect_Per_Pin FROM ( SELECT Pin_Ports.Pin_ID, COUNT(Pin_Port_Rectangles.Rect_ID) AS Rect_Count FROM Pin_Port_Rectangles JOIN Pin_Ports ON Pin_Port_Rectangles.Port_ID = Pin_Ports.Port_ID JOIN Pins ON Pin_Ports.Pin_ID = Pins.Pin_ID JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = 'sky130_fd_sc_hdll' GROUP BY Pin_Ports.Pin_ID ) AS Rect_Per_Pin JOIN Pins ON Rect_Per_Pin.Pin_ID = Pins.Pin_ID GROUP BY Pins.Macro_ID ) AS Avg_Rect_Per_Pin_Macro ON Macros.Macro_ID = Avg_Rect_Per_Pin_Macro.Macro_ID ORDER BY Avg_Rect_Per_Pin_Macro.Avg_Rect_Per_Pin DESC LIMIT 1",
    "SELECT Layer FROM Obstructions WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hdll__a22o_1')",
    "SELECT COUNT(*) AS Num_Obstruction_Rectangles FROM Obstruction_Rectangles WHERE Obstruction_ID IN (SELECT Obstruction_ID FROM Obstructions WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hdll__a21boi_1' AND Cell_Library = 'sky130_fd_sc_hdll'))",
    "SELECT Size_Width, Cell_Library FROM Macros WHERE Name = 'sky130_fd_sc_hd__nand2_1' OR Name = 'sky130_fd_sc_hdll__nand2_1'",
    "SELECT Cell_Library FROM Macros WHERE Name LIKE '%__nand2_1' ORDER BY Size_Width ASC LIMIT 1", 
    "SELECT Resistance_Per_SQ FROM Routing_Layers WHERE Name = 'met1' AND Cell_Library = 'sky130_fd_sc_hdll' AND Corner IN ('nom', 'min', 'max')",
    "SELECT Resistance FROM Cut_Layers WHERE Name = 'via2' AND Cell_Library = 'sky130_fd_sc_hdll' AND Corner IN ('min', 'max')",
    "SELECT Pitch_X FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hdll' UNION SELECT Pitch_X FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hs'",
    "SELECT Width FROM Routing_Layers WHERE Name = 'met1' AND Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom'",
    "SELECT COUNT(*) FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom'",
    "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom'",
    "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom' ORDER BY Thickness DESC;",
    "SELECT Name FROM Routing_Layers WHERE Type = 'ROUTING' AND Direction = 'VERTICAL' AND Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom';",
    "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom' ORDER BY Width DESC",
    "SELECT X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Side_Area_Ratios WHERE Routing_Layer_ID = (SELECT Layer_ID FROM Routing_Layers WHERE Name = 'met1' AND Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hdll')",
    "SELECT r.Name, a.X1, a.Y1, a.X2, a.Y2, a.X3, a.Y3, a.X4, a.Y4 FROM Routing_Layers r JOIN Antenna_Diff_Side_Area_Ratios a ON r.Layer_ID = a.Routing_Layer_ID WHERE r.Cell_Library = 'sky130_fd_sc_hdll' AND r.Corner = 'nom'",
    "SELECT Direction, AVG(Pitch_X) as Avg_Pitch_X, AVG(Pitch_Y) as Avg_Pitch_Y FROM Routing_Layers GROUP BY Direction",
    "SELECT Corner, AVG(Resistance_Per_SQ) AS Average_Resistance_Per_SQ FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hdll' GROUP BY Corner;",
    "SELECT Direction, AVG(AC_Current_Density_Rms) as Average_AC_Current_Density FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom' GROUP BY Direction; ",
    "SELECT COUNT(*) FROM Cut_Layers WHERE Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hdll'",
    "SELECT X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Area_Ratios WHERE Cut_Layer_ID  = (SELECT Layer_ID FROM Cut_Layers WHERE Name = 'via2' AND Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hdll')",
    "SELECT Name FROM Vias WHERE Via_ID IN (SELECT Via_ID FROM Via_Layers WHERE Layer_Name = 'mcon') AND Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom'",
    "SELECT Cut_Layers.Name, Antenna_Diff_Area_Ratios.X1, Antenna_Diff_Area_Ratios.Y1, Antenna_Diff_Area_Ratios.X2, Antenna_Diff_Area_Ratios.Y2, Antenna_Diff_Area_Ratios.X3, Antenna_Diff_Area_Ratios.Y3, Antenna_Diff_Area_Ratios.X4, Antenna_Diff_Area_Ratios.Y4 FROM Cut_Layers JOIN Antenna_Diff_Area_Ratios ON Cut_Layers.Layer_ID = Antenna_Diff_Area_Ratios.Cut_Layer_ID WHERE Cut_Layers.Cell_Library = 'sky130_fd_sc_hdll' AND Cut_Layers.Corner = 'nom'",
    "SELECT Corner, AVG(Resistance) AS Average_Resistance FROM Cut_Layers WHERE Cell_Library = 'sky130_fd_sc_hdll' GROUP BY Corner",
    "SELECT Corner, AVG(DC_Current_Density) AS Average_DC_Current FROM Cut_Layers WHERE Cell_Library = 'sky130_fd_sc_hdll' GROUP BY Corner",
    "SELECT COUNT(*) FROM Vias WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom' AND Upper_Layer = 'met5';",
    "SELECT vl.Layer_Name FROM Via_Layers vl JOIN Vias v ON vl.Via_ID = v.Via_ID WHERE v.Name = 'M1M2_PR' AND v.Cell_Library = 'sky130_fd_sc_hdll' AND v.Corner = 'nom'",
    "SELECT Upper_Layer, Lower_Layer, COUNT(*) AS Via_Count FROM Vias WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Corner = 'nom' GROUP BY Upper_Layer, Lower_Layer;",
    "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll');",
    "SELECT Area FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name = 'sky130_fd_sc_hdll__nand2_1'",
    "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') ORDER BY Area ASC LIMIT 1",
    "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Temperature = 25.0 AND Voltage = 1.8) ORDER BY Area ASC LIMIT 1 OFFSET 1;",
    "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') ORDER BY Leakage_Power ASC LIMIT 1;",
    "SELECT o.Cell_Library, COUNT(c.Cell_ID) AS Number_of_Cells FROM Cells AS c JOIN Operating_Conditions AS o ON c.Condition_ID = o.Condition_ID WHERE o.Temperature = 25.0 AND o.Voltage = 1.8 GROUP BY o.Cell_Library;",
    "SELECT oc.Cell_Library, AVG(c.Leakage_Power) AS Average_Leakage_Power FROM Cells AS c JOIN Operating_Conditions AS oc ON c.Condition_ID = oc.Condition_ID WHERE oc.Temperature = 25.0 AND oc.Voltage = 1.8 AND oc.Cell_Library IN ('sky130_fd_sc_hd', 'sky130_fd_sc_hdll', 'sky130_fd_sc_hs', 'sky130_fd_sc_ls', 'sky130_fd_sc_ms', 'sky130_fd_sc_lp') GROUP BY oc.Cell_Library;",
    "SELECT COUNT(Input_Pin_ID) AS Number_of_Input_Pins FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__o221a_4')",
    "SELECT Input_Pin_Name FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name = 'sky130_fd_sc_hdll__o22ai_4')",
    "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Input_Pins WHERE Clock = True AND Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll'));",
    "SELECT Input_Pin_Name, Rise_Capacitance, Fall_Capacitance FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__a22o_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll'));",
    "SELECT Input_Pin_Name FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__a22o_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll')) ORDER BY Fall_Capacitance ASC LIMIT 1",
    "SELECT Cells.Name AS Cell_Name, Input_Pins.Capacitance AS Input_Pin_Capacitance FROM Cells JOIN Input_Pins ON Cells.Cell_ID = Input_Pins.Cell_ID WHERE Cells.Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') ORDER BY Input_Pin_Capacitance DESC LIMIT 1",
    "SELECT Clock, AVG(Capacitance) AS Average_Capacitance FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll')) GROUP BY Clock",
    "SELECT AVG(Fall_Capacitance) AS Average_Fall_Capacitance, AVG(Rise_Capacitance) AS Average_Rise_Capacitance FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll')) AND Clock = 1",
    "SELECT Max_Transition AS Max_Transition FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__a32oi_4' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll'))",
    "SELECT Function FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__a22o_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll'))",
    "SELECT Max_Capacitance FROM Output_Pins JOIN Cells ON Output_Pins.Cell_ID = Cells.Cell_ID WHERE Cells.Name = 'sky130_fd_sc_hdll__nand2_1' AND Cells.Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll' );",
    "SELECT Name FROM ( SELECT c.Cell_ID, c.Name, op.Max_Capacitance FROM Cells c JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE c.Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Temperature = 25.0 AND Voltage = 1.8) ) ORDER BY Max_Capacitance DESC LIMIT 1;",
    "SELECT c.Name FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE oc.Cell_Library ='sky130_fd_sc_hdll' AND oc.Temperature = 25 AND oc.Voltage = 1.8 ORDER BY op.Max_Transition ASC LIMIT 1;",
    "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Cell_ID IN (SELECT Cell_ID FROM Output_Pins GROUP BY Cell_ID HAVING COUNT(Output_Pin_ID) > 1)",
    "SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__nand2_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll' ) ) AND Output_Pin_ID = ( SELECT Output_Pin_ID FROM Output_Pins WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__nand2_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll' ) ) ) AND Related_Input_Pin = 'A' AND Output_Capacitance = 0.0005 AND Input_Transition = 0.01"        ,
    "SELECT Rise_Delay, Fall_Delay FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__nand2_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll' ) ) AND Output_Pin_ID = ( SELECT Output_Pin_ID FROM Output_Pins WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__nand2_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll' ) ) ) AND Related_Input_Pin = 'A' AND Input_Transition = 1.5 AND Output_Capacitance = 0.161143;"   ,     
    "SELECT Related_Input_Pin FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__nand2_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll' ) ) AND Input_Transition = 0.01 AND Output_Capacitance = 0.0005 ORDER BY Fall_Delay ASC LIMIT 1;",
    "SELECT MIN(Fall_Delay) AS Minimum_Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__and2_1' AND Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll'))"        ,
    "SELECT (SELECT Max_Capacitance FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name LIKE 'sky130_fd_sc_hdll__and2_1')) AS High_Speed_Capacitance, (SELECT Max_Capacitance FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name LIKE 'sky130_fd_sc_hdll__and2_1')) AS Medium_Speed_Capacitance;",
    "SELECT (SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__nand2_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll')) AND Output_Capacitance = 0.0005 AND Input_Transition = 0.01 AND Related_Input_Pin = 'S') AS HD_Fall_Delay, (SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__mux2_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll')) AND Output_Capacitance = 0.0005 AND Input_Transition = 0.01 AND Related_Input_Pin = 'S') AS HDLL_Fall_Delay",
]


test_queries_tsmc65 = [
    "SELECT Size_Height FROM Macros WHERE Name = 'AO2B2X2MTH'",
    "SELECT Size_Width FROM Macros WHERE Name = 'ADDFHX1MTH'",
    "SELECT Size_Height FROM Macros WHERE Cell_Library = 'sc8_cln65gp_hvt' LIMIT 1",
    "SELECT Name FROM Macros  WHERE Cell_Library = 'sc8_cln65gp_hvt' ORDER BY Size_Width DESC LIMIT 1",
    "SELECT Name FROM Macros WHERE Cell_Library = 'sc8_cln65gp_hvt' ORDER BY Size_Width LIMIT 1",
    "SELECT Cell_Library, AVG(Size_Width) AS Average_Width FROM Macros GROUP BY Cell_Library",
    "SELECT Antenna_Gate_Area FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDFHX1MTH') AND Direction = 'INPUT'",
    "SELECT Antenna_Diff_Area  FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDFHX1MTH') AND Direction = 'OUTPUT'",
    "SELECT Name FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDFXLMTH' AND Cell_Library = 'sc8_cln65gp_hvt') AND (Use = 'ground' OR Use = 'power')",
    "SELECT Macros.Name AS Cell_Name, SUM(Pins.Antenna_Gate_Area) AS Total_Antenna_Gate_Area FROM Pins JOIN Pin_Ports ON Pins.Pin_ID = Pin_Ports.Pin_ID JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = 'sc8_cln65gp_hvt' GROUP BY Macros.Name ORDER BY Total_Antenna_Gate_Area DESC LIMIT 1",
    "SELECT pp.Layer FROM Pins p JOIN Pin_Ports pp ON p.Pin_ID = pp.Pin_ID WHERE p.Name = 'A' AND p.Direction = 'INPUT' AND p.Macro_ID IN (SELECT m.Macro_ID FROM Macros m WHERE m.Cell_Library ='sc8_cln65gp_hvt' and m.Name='ADDFXLMTH');",
    "SELECT Layer FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDFHX1MTH' AND Cell_Library = 'sc8_cln65gp_hvt') AND Use IN ('power', 'ground'))",
    "SELECT Name, Size_Width, Size_Height, (Size_Width * Size_Height) AS Total_Area FROM Macros WHERE Macro_ID = ( SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Macro_ID IN (SELECT Macro_ID FROM Pins WHERE Use = 'clock') ORDER BY (Size_Width * Size_Height) DESC LIMIT 1 )",
    "SELECT DISTINCT Layer FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Use = 'clock' AND Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sc8_cln65gp_hvt')) ",
    "SELECT Layer, COUNT(Pin_ID) AS Input_Pin_Count FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Direction = 'INPUT' AND Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sc8_cln65gp_hvt')) GROUP BY Layer",
    "SELECT DISTINCT m.Name AS Macro_Name FROM Macros m JOIN Pins p ON m.Macro_ID = p.Macro_ID JOIN Pin_Ports pp ON p.Pin_ID = pp.Pin_ID WHERE pp.Layer = 'M1' ORDER BY m.Name;",
    "SELECT Rect_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2 FROM Pin_Port_Rectangles WHERE Port_ID = (SELECT Port_ID FROM Pin_Ports WHERE Pin_ID = (SELECT Pin_ID FROM Pins WHERE Name = 'A' AND Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDFXLMTH')))",
    "SELECT Macros.Name FROM Macros JOIN ( SELECT Pins.Macro_ID, AVG(Rect_Count) AS Avg_Rect_Per_Pin FROM ( SELECT Pin_Ports.Pin_ID, COUNT(Pin_Port_Rectangles.Rect_ID) AS Rect_Count FROM Pin_Port_Rectangles JOIN Pin_Ports ON Pin_Port_Rectangles.Port_ID = Pin_Ports.Port_ID JOIN Pins ON Pin_Ports.Pin_ID = Pins.Pin_ID JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = 'sc8_cln65gp_hvt' GROUP BY Pin_Ports.Pin_ID ) AS Rect_Per_Pin JOIN Pins ON Rect_Per_Pin.Pin_ID = Pins.Pin_ID GROUP BY Pins.Macro_ID ) AS Avg_Rect_Per_Pin_Macro ON Macros.Macro_ID = Avg_Rect_Per_Pin_Macro.Macro_ID ORDER BY Avg_Rect_Per_Pin_Macro.Avg_Rect_Per_Pin DESC LIMIT 1",
    "SELECT Layer FROM Obstructions WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'AO2B2X2MTH')",
    "SELECT COUNT(*) AS Num_Obstruction_Rectangles FROM Obstruction_Rectangles WHERE Obstruction_ID IN (SELECT Obstruction_ID FROM Obstructions WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'AO2B2X2MTH' AND Cell_Library = 'sc8_cln65gp_hvt'))",
    "SELECT Size_Width, Cell_Library FROM Macros WHERE Name = 'ADDFHX1MTH' OR Name = 'AO2B2X2MTH'",
    "SELECT Cell_Library FROM Macros WHERE Name LIKE 'AO2B2X2MTH' ORDER BY Size_Width ASC LIMIT 1",
    "SELECT Resistance_Per_SQ FROM Routing_Layers WHERE Name = 'M1' AND Cell_Library = 'sc8_cln65gp_hvt' AND Corner IN ('CN65S_6M_3X2Z', 'CN65S_6M_4X1Z', 'CN65S_7M_4X2Y')",
    "SELECT Resistance FROM Cut_Layers WHERE Name = 'VIA2' AND Cell_Library = 'sc8_cln65gp_hvt' AND Corner IN ('CN65S_6M_3X2Z', 'CN65S_6M_4X1Z')",
    "SELECT Pitch_X FROM Routing_Layers WHERE Name = 'M1' AND Cell_Library = 'sc8_cln65gp_rvt' UNION SELECT Pitch_X FROM Routing_Layers WHERE Name = 'M1' AND Cell_Library = 'sc8_cln65gp_hvt'",
    "SELECT Width FROM Routing_Layers WHERE Name = 'M1' AND Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z'",
    "SELECT COUNT(*) FROM Routing_Layers WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z'",
    "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z'",
    "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z' ORDER BY Thickness DESC;",
    "SELECT Name FROM Routing_Layers WHERE Type = 'ROUTING' AND Direction = 'VERTICAL' AND Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z';",
    "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z' ORDER BY Width DESC",
    "SELECT X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Side_Area_Ratios WHERE Routing_Layer_ID = (SELECT Layer_ID FROM Routing_Layers WHERE Name = 'M1' AND Corner = 'CN65S_6M_3X2Z' AND Cell_Library = 'sc8_cln65gp_hvt')",
    "SELECT r.Name, a.X1, a.Y1, a.X2, a.Y2, a.X3, a.Y3, a.X4, a.Y4 FROM Routing_Layers r JOIN Antenna_Diff_Side_Area_Ratios a ON r.Layer_ID = a.Routing_Layer_ID WHERE r.Cell_Library = 'sc8_cln65gp_hvt' AND r.Corner = 'CN65S_6M_3X2Z'",
    "SELECT Direction, AVG(Pitch_X) as Avg_Pitch_X, AVG(Pitch_Y) as Avg_Pitch_Y FROM Routing_Layers GROUP BY Direction",
    "SELECT Corner, AVG(Resistance_Per_SQ) AS Average_Resistance_Per_SQ FROM Routing_Layers WHERE Cell_Library = 'sc8_cln65gp_hvt' GROUP BY Corner;",
    "SELECT Direction, AVG(AC_Current_Density_Rms) as Average_AC_Current_Density FROM Routing_Layers WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z' GROUP BY Direction; ",
    "SELECT COUNT(*) FROM Cut_Layers WHERE Corner = 'nom' AND Cell_Library = 'sc8_cln65gp_hvt'",
    "SELECT X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Area_Ratios WHERE Cut_Layer_ID  = (SELECT Layer_ID FROM Cut_Layers WHERE Name = 'VIA2' AND Corner = 'CN65S_6M_3X2Z' AND Cell_Library = 'sc8_cln65gp_hvt')",
    "SELECT Name FROM Vias WHERE Via_ID IN (SELECT Via_ID FROM Via_Layers WHERE Layer_Name = 'VIA3') AND Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z'",
    "SELECT Cut_Layers.Name, Antenna_Diff_Area_Ratios.X1, Antenna_Diff_Area_Ratios.Y1, Antenna_Diff_Area_Ratios.X2, Antenna_Diff_Area_Ratios.Y2, Antenna_Diff_Area_Ratios.X3, Antenna_Diff_Area_Ratios.Y3, Antenna_Diff_Area_Ratios.X4, Antenna_Diff_Area_Ratios.Y4 FROM Cut_Layers JOIN Antenna_Diff_Area_Ratios ON Cut_Layers.Layer_ID = Antenna_Diff_Area_Ratios.Cut_Layer_ID WHERE Cut_Layers.Cell_Library = 'sc8_cln65gp_hvt' AND Cut_Layers.Corner = 'CN65S_6M_3X2Z'",
    "SELECT Corner, AVG(Resistance) AS Average_Resistance FROM Cut_Layers WHERE Cell_Library = 'sc8_cln65gp_hvt' GROUP BY Corner",
    "SELECT Corner, AVG(DC_Current_Density) AS Average_DC_Current FROM Cut_Layers WHERE Cell_Library = 'sc8_cln65gp_hvt' GROUP BY Corner",
    "SELECT COUNT(*) FROM Vias WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'nom' AND Upper_Layer = 'M3';",
    "SELECT vl.Layer_Name FROM Via_Layers vl JOIN Vias v ON vl.Via_ID = v.Via_ID WHERE v.Name = 'VIA1_0_X2E_HV' AND v.Cell_Library = 'sc8_cln65gp_hvt' AND v.Corner = 'CN65S_6M_4X1Z'",
    "SELECT Upper_Layer, Lower_Layer, COUNT(*) AS Via_Count FROM Vias WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_4X1Z' GROUP BY Upper_Layer, Lower_Layer;",
    "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sc8_cln65gp_hvt');",
    "SELECT Area FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt') AND Name = 'ADDFXLMTH'",
    "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt') ORDER BY Area ASC LIMIT 1",
    "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Temperature = 25.0 AND Voltage = 1.0) ORDER BY Area ASC LIMIT 1 OFFSET 1;",
    "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt') ORDER BY Leakage_Power ASC LIMIT 1;",
    "SELECT o.Cell_Library, COUNT(c.Cell_ID) AS Number_of_Cells FROM Cells AS c JOIN Operating_Conditions AS o ON c.Condition_ID = o.Condition_ID WHERE o.Temperature = 25.0 AND o.Voltage = 1.0 GROUP BY o.Cell_Library;",
    "SELECT oc.Cell_Library, AVG(c.Leakage_Power) AS Average_Leakage_Power FROM Cells AS c JOIN Operating_Conditions AS oc ON c.Condition_ID = oc.Condition_ID WHERE oc.Temperature = 25.0 AND oc.Voltage = 1.0 AND oc.Cell_Library IN ('sc8_cln65gp_hvt', 'sc8_cln65gp_rvt', 'sc10_cln65gp_hvt', 'sc10_cln65gp_lvt', 'sc10_pmk', 'cln65gp', 'cln65gplus_lvt', 'cln65gplus_rvt') GROUP BY oc.Cell_Library;",
    "SELECT COUNT(Input_Pin_ID) AS Number_of_Input_Pins FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'AO2B2X2MTH')",
    "SELECT Input_Pin_Name FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt') AND Name = 'AO2B2X2MTH')",
    "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt'));",
    "SELECT Input_Pin_Name, Rise_Capacitance, Fall_Capacitance FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'AO2B2X2MTH' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt'));",
    "SELECT Input_Pin_Name FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDFHX1MTH' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt')) ORDER BY Fall_Capacitance ASC LIMIT 1",
    "SELECT Cells.Name AS Cell_Name, Input_Pins.Capacitance AS Input_Pin_Capacitance FROM Cells JOIN Input_Pins ON Cells.Cell_ID = Input_Pins.Cell_ID WHERE Cells.Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt') ORDER BY Input_Pin_Capacitance DESC LIMIT 1",
    "SELECT Clock, AVG(Capacitance) AS Average_Capacitance FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt')) GROUP BY Clock",
    "SELECT AVG(Fall_Capacitance) AS Average_Fall_Capacitance, AVG(Rise_Capacitance) AS Average_Rise_Capacitance FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt')) AND Clock = 1",
    "SELECT Max_Transition AS Max_Transition FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'AO2B2X2MTH' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt'))",
    "SELECT Function FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'AO2B2X2MTH' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt'))",
    "SELECT Max_Capacitance FROM Output_Pins JOIN Cells ON Output_Pins.Cell_ID = Cells.Cell_ID WHERE Cells.Name = 'AO2B2X2MTH' AND Cells.Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt' );",
    "SELECT Name FROM ( SELECT c.Cell_ID, c.Name, op.Max_Capacitance FROM Cells c JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE c.Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Temperature = 25.0 AND Voltage = 1.0) ) ORDER BY Max_Capacitance DESC LIMIT 1;",
    "SELECT c.Name FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE oc.Cell_Library ='sc8_cln65gp_hvt' AND oc.Temperature = 25 AND oc.Voltage = 1.0 ORDER BY op.Max_Transition ASC LIMIT 1;",
    "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt') AND Cell_ID IN (SELECT Cell_ID FROM Output_Pins GROUP BY Cell_ID HAVING COUNT(Output_Pin_ID) > 1)",
    "SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDFHX1MTH' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt' ) ) AND Output_Pin_ID = ( SELECT Output_Pin_ID FROM Output_Pins WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDFHX1MTH' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt' ) ) ) AND Related_Input_Pin = 'A' AND Output_Capacitance = 0.000486219 AND Input_Transition = 0.03052"        ,
    "SELECT Rise_Delay, Fall_Delay FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDFHX1MTH' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt' ) ) AND Output_Pin_ID = ( SELECT Output_Pin_ID FROM Output_Pins WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDFHX1MTH' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt' ) ) ) AND Related_Input_Pin = 'A' AND Input_Transition = 0.03052 AND Output_Capacitance = 0.000486219 ;"   ,     
    "SELECT Related_Input_Pin FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDFHX1MTH' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt' ) ) AND Input_Transition = 0.03052 AND Output_Capacitance = 0.000486219 ORDER BY Fall_Delay ASC LIMIT 1;",
    "SELECT MIN(Fall_Delay) AS Minimum_Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'AO2B2X2MTH' AND Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt'))"        ,
    "SELECT (SELECT Max_Capacitance FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt') AND Name LIKE 'ADDFHX1MTH')) AS High_Speed_Capacitance, (SELECT Max_Capacitance FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc10_cln65gp_lvt') AND Name LIKE 'ADDFHX1MTH')) AS Medium_Speed_Capacitance;",
    "SELECT (SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDFHX1MTH' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt')) AND Output_Capacitance = 0.000486219 AND Input_Transition = 0.03052 AND Related_Input_Pin = 'A') AS HD_Fall_Delay, (SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__mux2_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.0 AND Cell_Library = 'sc8_cln65gp_hvt')) AND Output_Capacitance = 0.000486219 AND Input_Transition = 0.03052 AND Related_Input_Pin = 'A') AS HDLL_Fall_Delay",
]



test_queries_gf12 = [
    "SELECT Size_Height FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14'",
    "SELECT Size_Width FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14'",
    "SELECT Size_Height FROM Macros WHERE Cell_Library = '14LPPXL_LVT' LIMIT 1",
    "SELECT Name FROM Macros  WHERE Cell_Library = '14LPPXL_LVT' ORDER BY Size_Width DESC LIMIT 1",
    "SELECT Name FROM Macros WHERE Cell_Library = '14LPPXL_LVT' ORDER BY Size_Width LIMIT 1",
    "SELECT Cell_Library, AVG(Size_Width) AS Average_Width FROM Macros GROUP BY Cell_Library",
    "SELECT Antenna_Gate_Area FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14') AND Direction = 'INPUT'",
    "SELECT Antenna_Diff_Area  FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14') AND Direction = 'OUTPUT'",
    "SELECT Name FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Cell_Library = '14LPPXL_LVT') AND (Use = 'GROUND' OR Use = 'POWER')",
    "SELECT Macros.Name AS Cell_Name, SUM(Pins.Antenna_Gate_Area) AS Total_Antenna_Gate_Area FROM Pins JOIN Pin_Ports ON Pins.Pin_ID = Pin_Ports.Pin_ID JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = '14LPPXL_LVT' GROUP BY Macros.Name ORDER BY Total_Antenna_Gate_Area DESC LIMIT 1",
    "SELECT pp.Layer FROM Pins p JOIN Pin_Ports pp ON p.Pin_ID = pp.Pin_ID WHERE p.Name = 'A' AND p.Direction = 'INPUT' AND p.Macro_ID IN (SELECT m.Macro_ID FROM Macros m WHERE m.Cell_Library ='14LPPXL_LVT' and m.Name='ADDH_X2N_A9PP84TL_C14');",
    "SELECT Layer FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Cell_Library = '14LPPXL_LVT') AND Use IN ('POWER', 'GROUND'))",
    "SELECT Name, Size_Width, Size_Height, (Size_Width * Size_Height) AS Total_Area FROM Macros WHERE Macro_ID = ( SELECT Macro_ID FROM Macros WHERE Cell_Library = '14LPPXL_LVT' AND Macro_ID IN (SELECT Macro_ID FROM Pins WHERE Use = 'CLOCK') ORDER BY (Size_Width * Size_Height) DESC LIMIT 1 )",
    "SELECT DISTINCT Layer FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Use = 'CLOCK' AND Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = '14LPPXL_LVT')) ",
    "SELECT Layer, COUNT(Pin_ID) AS Input_Pin_Count FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Direction = 'INPUT' AND Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = '14LPPXL_LVT')) GROUP BY Layer",
    "SELECT DISTINCT m.Name AS Macro_Name FROM Macros m JOIN Pins p ON m.Macro_ID = p.Macro_ID JOIN Pin_Ports pp ON p.Pin_ID = pp.Pin_ID WHERE pp.Layer = 'M1' ORDER BY m.Name;",
    "SELECT Rect_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2 FROM Pin_Port_Rectangles WHERE Port_ID = (SELECT Port_ID FROM Pin_Ports WHERE Pin_ID = (SELECT Pin_ID FROM Pins WHERE Name = 'A' AND Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14')))",
    "SELECT Macros.Name FROM Macros JOIN ( SELECT Pins.Macro_ID, AVG(Rect_Count) AS Avg_Rect_Per_Pin FROM ( SELECT Pin_Ports.Pin_ID, COUNT(Pin_Port_Rectangles.Rect_ID) AS Rect_Count FROM Pin_Port_Rectangles JOIN Pin_Ports ON Pin_Port_Rectangles.Port_ID = Pin_Ports.Port_ID JOIN Pins ON Pin_Ports.Pin_ID = Pins.Pin_ID JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = '14LPPXL_LVT' GROUP BY Pin_Ports.Pin_ID ) AS Rect_Per_Pin JOIN Pins ON Rect_Per_Pin.Pin_ID = Pins.Pin_ID GROUP BY Pins.Macro_ID ) AS Avg_Rect_Per_Pin_Macro ON Macros.Macro_ID = Avg_Rect_Per_Pin_Macro.Macro_ID ORDER BY Avg_Rect_Per_Pin_Macro.Avg_Rect_Per_Pin DESC LIMIT 1",
    "SELECT Layer FROM Obstructions WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14')",
    "SELECT COUNT(*) AS Num_Obstruction_Rectangles FROM Obstruction_Rectangles WHERE Obstruction_ID IN (SELECT Obstruction_ID FROM Obstructions WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Cell_Library = '14LPPXL_LVT'))",
    "SELECT Size_Width, Cell_Library FROM Macros WHERE Name = 'ADDH_X2N_A9PP84TL_C14' OR Name = 'ADDH_X2N_A9PP84TL_C14'",
    "SELECT Cell_Library FROM Macros WHERE Name LIKE 'ADDH_X2N_A9PP84TL_C14' ORDER BY Size_Width ASC LIMIT 1",
    "SELECT Resistance_Per_SQ FROM Routing_Layers WHERE Name = 'M1' AND Cell_Library = '14LPPXL_LVT' AND Corner IN ('CN65S_6M_3X2Z', 'CN65S_6M_4X1Z', 'CN65S_7M_4X2Y')",
    "SELECT Resistance FROM Cut_Layers WHERE Name = 'VIA2' AND Cell_Library = '14LPPXL_LVT' AND Corner IN ('CN65S_6M_3X2Z', 'CN65S_6M_4X1Z')",
    "SELECT Pitch_X FROM Routing_Layers WHERE Name = 'M1' AND Cell_Library = '14LPPXL_LVT' UNION SELECT Pitch_X FROM Routing_Layers WHERE Name = 'M1' AND Cell_Library = 'sc8_cln65gp_hvt'",
    "SELECT Width FROM Routing_Layers WHERE Name = 'M1' AND Cell_Library = '14LPPXL_LVT' AND Corner = 'CN65S_6M_3X2Z'",
    "SELECT COUNT(*) FROM Routing_Layers WHERE Cell_Library = '14LPPXL_LVT' AND Corner = 'CN65S_6M_3X2Z'",
    "SELECT Name FROM Routing_Layers WHERE Cell_Library = '14LPPXL_LVT' AND Corner = 'CN65S_6M_3X2Z'",
    "SELECT Name FROM Routing_Layers WHERE Cell_Library = '14LPPXL_LVT' AND Corner = 'CN65S_6M_3X2Z' ORDER BY Thickness DESC;",
    "SELECT Name FROM Routing_Layers WHERE Type = 'ROUTING' AND Direction = 'VERTICAL' AND Cell_Library = '14LPPXL_LVT' AND Corner = 'CN65S_6M_3X2Z';",
    "SELECT Name FROM Routing_Layers WHERE Cell_Library = '14LPPXL_LVT' AND Corner = 'CN65S_6M_3X2Z' ORDER BY Width DESC",
    "SELECT X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Side_Area_Ratios WHERE Routing_Layer_ID = (SELECT Layer_ID FROM Routing_Layers WHERE Name = 'M1' AND Corner = 'CN65S_6M_3X2Z' AND Cell_Library = 'sc8_cln65gp_hvt')",
    "SELECT r.Name, a.X1, a.Y1, a.X2, a.Y2, a.X3, a.Y3, a.X4, a.Y4 FROM Routing_Layers r JOIN Antenna_Diff_Side_Area_Ratios a ON r.Layer_ID = a.Routing_Layer_ID WHERE r.Cell_Library = 'sc8_cln65gp_hvt' AND r.Corner = 'CN65S_6M_3X2Z'",
    "SELECT Direction, AVG(Pitch_X) as Avg_Pitch_X, AVG(Pitch_Y) as Avg_Pitch_Y FROM Routing_Layers GROUP BY Direction",
    "SELECT Corner, AVG(Resistance_Per_SQ) AS Average_Resistance_Per_SQ FROM Routing_Layers WHERE Cell_Library = '14LPPXL_LVT' GROUP BY Corner;",
    "SELECT Direction, AVG(AC_Current_Density_Rms) as Average_AC_Current_Density FROM Routing_Layers WHERE Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z' GROUP BY Direction; ",
    "SELECT COUNT(*) FROM Cut_Layers WHERE Corner = 'nom' AND Cell_Library = '14LPPXL_LVT'",
    "SELECT X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Area_Ratios WHERE Cut_Layer_ID  = (SELECT Layer_ID FROM Cut_Layers WHERE Name = 'VIA2' AND Corner = 'CN65S_6M_3X2Z' AND Cell_Library = 'sc8_cln65gp_hvt')",
    "SELECT Name FROM Vias WHERE Via_ID IN (SELECT Via_ID FROM Via_Layers WHERE Layer_Name = 'VIA3') AND Cell_Library = 'sc8_cln65gp_hvt' AND Corner = 'CN65S_6M_3X2Z'",
    "SELECT Cut_Layers.Name, Antenna_Diff_Area_Ratios.X1, Antenna_Diff_Area_Ratios.Y1, Antenna_Diff_Area_Ratios.X2, Antenna_Diff_Area_Ratios.Y2, Antenna_Diff_Area_Ratios.X3, Antenna_Diff_Area_Ratios.Y3, Antenna_Diff_Area_Ratios.X4, Antenna_Diff_Area_Ratios.Y4 FROM Cut_Layers JOIN Antenna_Diff_Area_Ratios ON Cut_Layers.Layer_ID = Antenna_Diff_Area_Ratios.Cut_Layer_ID WHERE Cut_Layers.Cell_Library = 'sc8_cln65gp_hvt' AND Cut_Layers.Corner = 'CN65S_6M_3X2Z'",
    "SELECT Corner, AVG(Resistance) AS Average_Resistance FROM Cut_Layers WHERE Cell_Library = '14LPPXL_LVT' GROUP BY Corner",
    "SELECT Corner, AVG(DC_Current_Density) AS Average_DC_Current FROM Cut_Layers WHERE Cell_Library = '14LPPXL_LVT' GROUP BY Corner",
    "SELECT COUNT(*) FROM Vias WHERE Cell_Library = '14LPPXL_LVT' AND Corner = 'nom' AND Upper_Layer = 'M3';",
    "SELECT vl.Layer_Name FROM Via_Layers vl JOIN Vias v ON vl.Via_ID = v.Via_ID WHERE v.Name = 'VIA1_0_X2E_HV' AND v.Cell_Library = '14LPPXL_LVT' AND v.Corner = 'CN65S_6M_4X1Z'",
    "SELECT Upper_Layer, Lower_Layer, COUNT(*) AS Via_Count FROM Vias WHERE Cell_Library = '14LPPXL_LVT' AND Corner = 'CN65S_6M_4X1Z' GROUP BY Upper_Layer, Lower_Layer;",
    "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6 AND Cell_Library = '14LPPXL_LVT');",
    "SELECT Area FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6 AND Cell_Library = '14LPPXL_LVT') AND Name = 'ADDH_X2N_A9PP84TL_C14'",
    "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT') ORDER BY Area ASC LIMIT 1",
    "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = '14LPPXL_LVT' AND Temperature = 25.0 AND Voltage = 0.6 ) ORDER BY Area ASC LIMIT 1 OFFSET 1;",
    "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT') ORDER BY Leakage_Power ASC LIMIT 1;",
    "SELECT o.Cell_Library, COUNT(c.Cell_ID) AS Number_of_Cells FROM Cells AS c JOIN Operating_Conditions AS o ON c.Condition_ID = o.Condition_ID WHERE o.Temperature = 25.0 AND o.Voltage = 0.6  GROUP BY o.Cell_Library;",
    "SELECT oc.Cell_Library, AVG(c.Leakage_Power) AS Average_Leakage_Power FROM Cells AS c JOIN Operating_Conditions AS oc ON c.Condition_ID = oc.Condition_ID WHERE oc.Temperature = 25.0 AND oc.Voltage = 0.6  AND oc.Cell_Library IN ('14LPPXL_LVT', '14LPPXL_SLVT') GROUP BY oc.Cell_Library;",
    "SELECT COUNT(Input_Pin_ID) AS Number_of_Input_Pins FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14')",
    "SELECT Input_Pin_Name FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT') AND Name = 'ADDH_X2N_A9PP84TL_C14')",
    "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT'));",
    "SELECT Input_Pin_Name, Rise_Capacitance, Fall_Capacitance FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT'));",
    "SELECT Input_Pin_Name FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT')) ORDER BY Fall_Capacitance ASC LIMIT 1",
    "SELECT Cells.Name AS Cell_Name, Input_Pins.Capacitance AS Input_Pin_Capacitance FROM Cells JOIN Input_Pins ON Cells.Cell_ID = Input_Pins.Cell_ID WHERE Cells.Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT') ORDER BY Input_Pin_Capacitance DESC LIMIT 1",
    "SELECT Clock, AVG(Capacitance) AS Average_Capacitance FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT')) GROUP BY Clock",  
    "SELECT AVG(Fall_Capacitance) AS Average_Fall_Capacitance, AVG(Rise_Capacitance) AS Average_Rise_Capacitance FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT')) AND Clock = 1",
    "SELECT Max_Transition AS Max_Transition FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT'))",
    "SELECT Function FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT'))",  
    "SELECT Max_Capacitance FROM Output_Pins JOIN Cells ON Output_Pins.Cell_ID = Cells.Cell_ID WHERE Cells.Name = 'ADDH_X2N_A9PP84TL_C14' AND Cells.Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT' );",
    "SELECT Name FROM ( SELECT c.Cell_ID, c.Name, op.Max_Capacitance FROM Cells c JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE c.Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = '14LPPXL_LVT' AND Temperature = 25.0 AND Voltage = 0.6 ) ) ORDER BY Max_Capacitance DESC LIMIT 1;",
    "SELECT c.Name FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE oc.Cell_Library ='14LPPXL_LVT' AND oc.Temperature = 25 AND oc.Voltage = 0.6  ORDER BY op.Max_Transition ASC LIMIT 1;",
    "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT') AND Cell_ID IN (SELECT Cell_ID FROM Output_Pins GROUP BY Cell_ID HAVING COUNT(Output_Pin_ID) > 1)",
    "SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT' ) ) AND Output_Pin_ID = ( SELECT Output_Pin_ID FROM Output_Pins WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT' ) ) ) AND Related_Input_Pin = 'A' AND Output_Capacitance = 0.396941 AND Input_Transition =1.44	"        ,
    "SELECT Rise_Delay, Fall_Delay FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT' ) ) AND Output_Pin_ID = ( SELECT Output_Pin_ID FROM Output_Pins WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT' ) ) ) AND Related_Input_Pin = 'A' AND Input_Transition = 1.44	 AND Output_Capacitance = 0.396941 ;"   ,     
    "SELECT Related_Input_Pin FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6 AND Cell_Library = '14LPPXL_LVT' ) ) AND Input_Transition = 1.44 AND Output_Capacitance = 0.396941 ORDER BY Fall_Delay ASC LIMIT 1;",
    "SELECT MIN(Fall_Delay) AS Minimum_Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT'))"        ,
    "SELECT (SELECT Max_Capacitance FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT') AND Name LIKE 'ADDH_X2N_A9PP84TL_C14')) AS High_Speed_Capacitance, (SELECT Max_Capacitance FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT') AND Name LIKE 'ADDH_X2N_A9PP84TL_C14')) AS Medium_Speed_Capacitance;",
    "SELECT (SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6  AND Cell_Library = '14LPPXL_LVT')) AND Output_Capacitance = 0.396941 AND Input_Transition =1.44 AND Related_Input_Pin = 'A') AS HD_Fall_Delay, (SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'ADDH_X2N_A9PP84TL_C14' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 0.6 AND Cell_Library = '14LPPXL_LVT')) AND Output_Capacitance = 0.396941 AND Input_Transition = 1.44	 AND Related_Input_Pin = 'A') AS HDLL_Fall_Delay",
]


def plot_all_execution_times(tsmc_sizes, tsmc_disk, tsmc_mem, sky130_sizes, sky130_disk, sky130_mem, save_path="./output/exec_time_all.png"):
    plt.figure(figsize=(10, 6))
    
    # TSMC 65nm curves
    plt.plot(tsmc_sizes, tsmc_disk, marker='o', linestyle='-', linewidth=2, color='blue', label="TSMC 65nm Disk")
    plt.plot(tsmc_sizes, tsmc_mem, marker='o', linestyle='--', linewidth=2, color='blue', label="TSMC 65nm In-Memory")
    
    # Sky130 130nm curves
    plt.plot(sky130_sizes, sky130_disk, marker='s', linestyle='-', linewidth=2, color='red', label="Sky130 130nm Disk")
    plt.plot(sky130_sizes, sky130_mem, marker='s', linestyle='--', linewidth=2, color='red', label="Sky130 130nm In-Memory")
    
    plt.title("Query Execution Time vs Database Size", fontsize=16)
    plt.xlabel("Database Size (GB)", fontsize=14)
    plt.ylabel("Execution Time (seconds)", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=12)
    plt.savefig(save_path)



# Re-import necessary libraries
import matplotlib.pyplot as plt
import numpy as np

# Compute correct fractions based on database sizes
def compute_fractions(database_sizes):
    max_size = max(database_sizes)  # Full PDK corresponds to the max database size
    fractions = [f"{round(size / max_size, 2)}" for size in database_sizes]
    return fractions

# Define function for plotting
def plot_with_secondary_x_axis_and_star(database_sizes, execution_times_in_memory, execution_times_on_disk, label, save_path):
    # Use 'ggplot' style
    plt.style.use('ggplot')

    # Compute correct fractions
    fractions = compute_fractions(database_sizes)

    # Create figure
    fig, ax1 = plt.subplots(figsize=(3.8, 2.85))

    # Primary X-axis (Database Size in GB)
    ax1.set_xlabel("Database Size (GB)", fontsize=14, color="black", labelpad=1)
    ax1.set_ylabel("Execution Time (sec)", fontsize=14, color="black", labelpad=1)
    ax1.grid(True, linestyle='--', linewidth=0.6, color="#d3d3d3")  # Subtle grid

    # Tick Labels
    ax1.tick_params(axis='both', labelsize=9, colors="black")

    # Execution Time Plots
    ax1.plot(database_sizes, execution_times_in_memory, marker='o', linestyle='-', linewidth=1.5, markersize=5, color='#1f77b4', label="In-Memory")
    ax1.plot(database_sizes, execution_times_on_disk, marker='s', linestyle='--', linewidth=1.5, markersize=5, color='#ff7f0e', label="On-Disk")

    # Highlight Full PDK with Star Marker
    ax1.scatter(database_sizes[-1], execution_times_in_memory[-1], marker='*', s=140, color='#1f77b4', edgecolors='black')
    ax1.scatter(database_sizes[-1], execution_times_on_disk[-1], marker='*', s=140, color='#ff7f0e', edgecolors='black')

    # Secondary X-axis for Fraction of PDK
    # ax2 = ax1.twiny()
    # ax2.set_xlim(ax1.get_xlim())  
    # ax2.set_xlabel("Fraction of PDK Size", fontsize=14, color="black", labelpad=3)

    # # Update Fraction Labels with Correct Values
    # ax2.set_xticks(database_sizes)
    # ax2.set_xticklabels(fractions, fontsize=9, color="black", rotation=0)

    # Custom Compact Legend (Inside the plot, upper-left corner)
    legend_elements = [
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='black', markersize=14, label=label),
        plt.Line2D([0], [0], linestyle='-', color='#1f77b4', label="In-Memory"),
        plt.Line2D([0], [0], linestyle='--', color='#ff7f0e', label="On-Disk"),
    ]

    ax1.legend(
        handles=legend_elements,
        fontsize=12,  # Smaller font for compactness
        loc='upper left',  # Inside the figure
        frameon=True,  # Add a slight background for readability
        handletextpad=0.5,  # Reduce spacing between legend marker and text
        columnspacing=0.7,  # Reduce spacing between columns
        borderaxespad=0.3  # Reduce padding within axes
    )

    # Layout and Save
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.show()


def load_database_in_memory(db_path):
    """
    Load a SQLite database into memory and return the in-memory SQLAlchemy engine.
    """
    disk_engine = create_engine(f"sqlite:///{db_path}")
    memory_engine = create_engine("sqlite:///:memory:")

    with disk_engine.connect() as disk_conn, memory_engine.connect() as mem_conn:
        for line in disk_conn.connection.iterdump():
            mem_conn.connection.execute(line)

    return memory_engine

def main():
    parser = argparse.ArgumentParser(description="Parse design files and output JSON")
    parser.add_argument('--dbs_sky130', type=list,
                        help='Path to Sky130 design files',
                        default=['./dbs/sky130_one.db', './dbs/sky130_two.db',
                                 './dbs/sky130_three.db', './dbs/sky130_four.db',
                                 './dbs/sky130_five.db', './dbs/sky130_six.db'])
    parser.add_argument('--dbs_tsmc', type=list,
                        help='Path to TSMC65 design files',
                        default=['./dbs/tsmc65_one/tsmc65_index.db', './dbs/tsmc65_two/tsmc65_index.db',
                                 './dbs/tsmc65_three/tsmc65_index.db', './dbs/tsmc65_four/tsmc65_index.db',
                                 './dbs/tsmc65_five/tsmc65_index.db', './dbs/tsmc65_six/tsmc65_index.db'])

    parser.add_argument('--dbs_gf12', type=list,
                        help='Path to TSMC65 design files',
                        default=['./dbs/gf12_one/gf12_index.db', './dbs/gf12_two/gf12_index.db',
                                 './dbs/gf12_three/gf12_index.db', './dbs/gf12_four/gf12_index.db',
                                 './dbs/gf12_five/gf12_index.db', './dbs/gf12_six/gf12_index.db'])
    parser.add_argument("--output_dir", help="Output directory", default='./output')
    args = parser.parse_args()  

    dbs_sky130 = args.dbs_sky130
    dbs_tsmc = args.dbs_tsmc
    dbs_gf12 = args.dbs_gf12
    output_dir = args.output_dir

    logger = get_logger("pdk_db.log")
    
    # --- Process Sky130 130nm databases ---
    sizes_gf12 = []
    exec_times_gf12_disk = []
    exec_times_gf12_mem = []
    
    for db in dbs_gf12:
        db_size = os.path.getsize(db)
        db_size_gb = db_size / (1024 * 1024 * 1024)
        sizes_gf12.append(db_size_gb)
        
        # Disk-based measurement
        database_disk = SQLDatabase.from_uri(f"sqlite:///{db[2:]}", view_support=True)
        avg_exec_time_disk = 0
        for query in test_queries_gf12:
            exec_time, _ = execute_query(query=query, database=database_disk)
            avg_exec_time_disk += exec_time
        exec_times_gf12_disk.append(avg_exec_time_disk)
        logger.info(f"GF12 Disk, Avg Exec Time = {avg_exec_time_disk}, Size = {db_size_gb} GB")
        
        # In-memory measurement
        memory_engine = load_database_in_memory(db)
        memory_db = SQLDatabase(engine=memory_engine)
        avg_exec_time_mem = 0
        for query in test_queries_gf12:
            exec_time, _ = execute_query(query=query, database=memory_db)
            avg_exec_time_mem += exec_time
        exec_times_gf12_mem.append(avg_exec_time_mem)
        logger.info(f"GF12 130nm In-Memory, Avg Exec Time = {avg_exec_time_mem}, Size = {db_size_gb} GB")
        
        memory_engine.dispose()
        del memory_engine, memory_db


    plot_with_secondary_x_axis_and_star(
        database_sizes=sizes_gf12,
        execution_times_in_memory=exec_times_gf12_mem,
        execution_times_on_disk=exec_times_gf12_disk,
        save_path="./output/exec_time_gf12.png",
        label="GF-LP 12nm"
    )


    # # --- Process Sky130 130nm databases ---
    # sizes_sky130 = []
    # exec_times_sky130_disk = []
    # exec_times_sky130_mem = []
    
    # for db in dbs_sky130:
    #     db_size = os.path.getsize(db)
    #     db_size_gb = db_size / (1024 * 1024 * 1024)
    #     sizes_sky130.append(db_size_gb)
        
    #     # Disk-based measurement
    #     database_disk = SQLDatabase.from_uri(f"sqlite:///{db[2:]}", view_support=True)
    #     avg_exec_time_disk = 0
    #     for query in test_queries_sky130:
    #         exec_time, _ = execute_query(query=query, database=database_disk)
    #         avg_exec_time_disk += exec_time
    #     exec_times_sky130_disk.append(avg_exec_time_disk)
    #     logger.info(f"Sky130 130nm Disk, Avg Exec Time = {avg_exec_time_disk}, Size = {db_size_gb} GB")
        
    #     # In-memory measurement
    #     memory_engine = load_database_in_memory(db)
    #     memory_db = SQLDatabase(engine=memory_engine)
    #     avg_exec_time_mem = 0
    #     for query in test_queries_sky130:
    #         exec_time, _ = execute_query(query=query, database=memory_db)
    #         avg_exec_time_mem += exec_time
    #     exec_times_sky130_mem.append(avg_exec_time_mem)
    #     logger.info(f"Sky130 130nm In-Memory, Avg Exec Time = {avg_exec_time_mem}, Size = {db_size_gb} GB")
        
    #     memory_engine.dispose()
    #     del memory_engine, memory_db


    

    # # --- Process TSMC 65nm databases ---
    # sizes_tsmc = []
    # exec_times_tsmc_disk = []
    # exec_times_tsmc_mem = []
    
    # for db in dbs_tsmc:
    #     # Get size in gigabytes
    #     db_size = os.path.getsize(db)
    #     db_size_gb = db_size / (1024 * 1024 * 1024)
    #     sizes_tsmc.append(db_size_gb)
        
    #     # Disk-based measurement
    #     # Note: db[2:] is used in your original code to adjust the path for SQLAlchemy URI
    #     database_disk = SQLDatabase.from_uri(f"sqlite:///{db[2:]}", view_support=True)
    #     avg_exec_time_disk = 0
    #     for query in test_queries_tsmc65:
    #         exec_time, _ = execute_query(query=query, database=database_disk)
    #         avg_exec_time_disk += exec_time
    #     exec_times_tsmc_disk.append(avg_exec_time_disk)
    #     logger.info(f"TSMC 65nm Disk, Avg Exec Time = {avg_exec_time_disk}, Size = {db_size_gb} GB")
        
    #     # In-memory measurement
    #     memory_engine = load_database_in_memory(db)
    #     memory_db = SQLDatabase(engine=memory_engine)
    #     avg_exec_time_mem = 0
    #     for query in test_queries_tsmc65:
    #         exec_time, _ = execute_query(query=query, database=memory_db)
    #         avg_exec_time_mem += exec_time
    #     exec_times_tsmc_mem.append(avg_exec_time_mem)
    #     logger.info(f"TSMC 65nm In-Memory, Avg Exec Time = {avg_exec_time_mem}, Size = {db_size_gb} GB")
        
    #     # Clean up in-memory engine
    #     memory_engine.dispose()
    #     del memory_engine, memory_db

  
    # # --- Plot all curves in one figure ---
    # plot_all_execution_times(
    #     tsmc_sizes=sizes_tsmc,
    #     tsmc_disk=exec_times_tsmc_disk,
    #     tsmc_mem=exec_times_tsmc_mem,
    #     sky130_sizes=sizes_sky130,
    #     sky130_disk=exec_times_sky130_disk,
    #     sky130_mem=exec_times_sky130_mem,
    #     save_path=os.path.join(output_dir, "exec_time_all.png")
    # )

    

    
    # plot_with_secondary_x_axis_and_star(
    #     database_sizes=sizes_sky130,
    #     execution_times_in_memory=exec_times_sky130_mem,
    #     execution_times_on_disk=exec_times_sky130_disk,
    #     save_path="./output/exec_time_sky130.png",
    #     label="Skywater 130nm"
    # )

    # plot_with_secondary_x_axis_and_star(
    #     database_sizes=sizes_tsmc,
    #     execution_times_in_memory=exec_times_tsmc_mem,
    #     execution_times_on_disk=exec_times_tsmc_disk,
    #     save_path="./output/exec_time_tsmc65.png",
    #     label="TSMC-CLN65GP 65nm"
    # )

if __name__ == '__main__':
    main()

