from core.agents.few_shot.demo import Demo

view_router_few_shot = [
    Demo(
        input="What is the area of the sky130_fd_sc_hd__nand2_1 cell?",
        source="Liberty",
        explain="This question is routed to the Liberty view because Liberty files (.lib) contain timing characteristics of cells, including their area. While Liberty files provide the overall area, they do not contain dimensional details like width and height. For area information, Liberty is the correct source.",
        route_query="""
```json
{{
    "explain": "This question is routed to the Liberty view because Liberty files (.lib) contain timing characteristics of cells, including their area. While Liberty files provide the overall area, they do not contain dimensional details like width and height. For area information, Liberty is the correct source.",
    "view": "Liberty"
}}
```
"""
    ).to_dict(),
    
    Demo(
        input="How many cells are in the PDK?",
        source="Liberty",
        explain="This question is routed to the Liberty view because Liberty files typically include entries for all cells available in a Process Design Kit (PDK). By counting the number of cell entries in the Liberty file, we can determine the total number of cells in the PDK. This view offers a comprehensive list of all standard cells and their timing properties.",
        route_query="""
```json
{{
    "explain": "This question is routed to the Liberty view because Liberty files typically include entries for all cells available in a Process Design Kit (PDK). By counting the number of cell entries in the Liberty file, we can determine the total number of cells in the PDK. This view offers a comprehensive list of all standard cells and their timing properties.",
    "view": "Liberty"
}}
```
"""
    ).to_dict(),
  
    Demo(
        input="What is the width of the sky130_fd_sc_hd__mux4_1 cell?",
        source="Lef",
        explain="This question is routed to the Lef (Library Exchange Format) view because Lef files contain physical layout information of cells, including their specific width and height dimensions. Unlike Liberty files, which provide timing characteristics and overall area, Lef files explicitly define the width and height of each cell. For dimensional queries like width or height, Lef is the primary source.",
        route_query="""
```json
{{
    "explain": "This question is routed to the Lef (Library Exchange Format) view because Lef files contain physical layout information of cells, including their specific width and height dimensions. Unlike Liberty files, which provide timing characteristics and overall area, Lef files explicitly define the width and height of each cell. For dimensional queries like width or height, Lef is the primary source.",
    "view": "Lef"
}}
```
"""
    ).to_dict(),
    
    Demo(
        input="Compare the width of the mux4_1 cell between all the standard cell libraries",
        source="Lef",
        explain="This question is asking to compare the width of the mux4_1 cell in all cell libraires, therefore it should be routed to the Lef view because it contain physical layout information of cells, including their specific width and height dimensions.",
        route_query="""
```json
{{
    "explain": "This question is asking to compare the width of the mux4_1 cell in all cell libraires, therefore it should be routed to the Lef view because it contain physical layout information of cells, including their specific width and height dimensions.",
    "view": "Lef"
}}
```
"""
    ).to_dict(),
    
    Demo(
        input="What is the met1 spacing rule?",
        source="TechnologyLef",
        explain="This question is routed to the TechnologyLef view because Technology Lef files contain process-specific design rules, including metal layer specifications. The TechnologyLef view provides detailed information about manufacturing constraints, such as minimum spacing requirements between metal lines on different layers. Neither Liberty nor standard Lef files contain this level of process-specific routing information.",
        route_query="""
```json
{{
    "explain": "This question is routed to the TechnologyLef view because Technology Lef files contain process-specific design rules, including metal layer specifications. The TechnologyLef view provides detailed information about manufacturing constraints, such as minimum spacing requirements between metal lines on different layers. Neither Liberty nor standard Lef files contain this level of process-specific routing information.",
    "view": "TechnologyLef"
}}
```
"""
    ).to_dict(),
]