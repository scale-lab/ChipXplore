from core.agents.few_shot.demo import Demo


# SCL Router Few-shot examples
scl_router_few_shot = [
    Demo(
        input="What is the propagation delay of the sky130_fd_sc_hd__nand2_1 cell with an output load capacitence of 0.0005 and input rise time of 0.01 ?",
        source="Liberty",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain": "This question should be routed to the HighDensity (HD) standard cell library because the cell name starts with sky130_fd_sc_hd.",
"HighDensity": "keep",
"HighDensityLowLeakage": "drop",
"HighSpeed": "drop",
"LowSpeed": "drop",
"MediumSpeed": "drop",
"LowPower": "drop"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),
    
    Demo(
        input="How many pins does the sky130_fd_sc_hs__mux4_1 have ?",
        source="Liberty",
        scl_variant="""
```json
{{
"Explain": "This question should be routed to the HighSpeed (HS) standard cell library because the cell name starts with sky130_fd_sc_hs.",
"HighDensity": "drop",
"HighDensityLowLeakage": "drop",
"HighSpeed": "keep",
"LowSpeed": "drop",
"MediumSpeed": "drop",
"LowPower": "drop"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
        
    ).to_dict(),
    
          
    Demo(
        input="List the input pin capacitence of the sky130_fd_sc_ls__and2_1 cell",
        source="Liberty",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain": "This question should be routed to the LowSpeed (LS) standard cell library because the cell name starts with sky130_fd_sc_ls.",
"HighDensity": "drop",
"HighDensityLowLeakage": "drop",
"HighSpeed": "drop",
"LowSpeed": "keep",
"MediumSpeed": "drop",
"LowPower": "drop"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),
    
          
    Demo(
        input="List the input pin capacitence of the sky130_fd_sc_hdll__nand2_1 cell",
        source="Liberty",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain": "This question should be routed to the HighDensityLowLeakage (HDLL) standard cell library because the cell name starts with sky130_fd_sc_hdll.",
"HighDensity": "drop",
"HighDensityLowLeakage": "keep",
"HighSpeed": "drop",
"LowSpeed": "drop",
"MediumSpeed": "drop",
"LowPower": "drop"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),
    
     Demo(
        input="What is the fall propagation delay of the sky130_fd_sc_ms__nand2_1 cell with an output load capacitence of 0.0005 and input rise time of 0.01 for the input pin A ?",
        source="Liberty",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain":"This question should be routed to the MediumSpeed (MS) standard cell library because the cell name starts with sky130_fd_sc_ms.",
"HighDensity": "drop",
"HighDensityLowLeakage": "drop",
"HighSpeed": "drop",
"LowSpeed": "drop",
"MediumSpeed": "keep",
"LowPower": "drop"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),
     
       
     Demo(
        input="List routing and cut layers in this PDK",
        source="TechnologyLef",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain": "This question didn't specifiy a specific library, so it should be routed to the HighDensity (HD) library",
"HighDensity": "keep",
"HighDensityLowLeakage": "drop",
"HighSpeed": "drop",
"LowSpeed": "drop",
"MediumSpeed": "drop",
"LowPower": "drop"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),
     
  Demo(
        input="What is the width of the met1 layer ?",
        source="TechnologyLef",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain": "This question didn't specifiy a specific library, so it should be routed to the HighDensity (HD) library",
"HighDensity": "keep",
"HighDensityLowLeakage": "drop",
"HighSpeed": "drop",
"LowSpeed": "drop",
"MediumSpeed": "drop",
"LowPower": "drop"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),

  Demo(
        input="Compare the met1 routing layer resistance between the three corners: nom, min, max",
        source="TechnologyLef",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain": "This question didn't specifiy a specific library, so it should be routed to the HighDensity (HD) library",
"HighDensity": "keep",
"HighDensityLowLeakage": "drop",
"HighSpeed": "drop",
"LowSpeed": "drop",
"MediumSpeed": "drop",
"LowPower": "drop"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),
  
    Demo(
        input="Compare the leakage power of the mux4_1 cell between the high density and high speed libraries.",
        source="Liberty",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain": "This question should be routed to the HighDensity (HD) and the HighSpeed (HS) libraries because the user wants to compare between the two libraries. ",
"HighDensity": "keep",
"HighDensityLowLeakage": "drop",
"HighSpeed": "keep",
"LowSpeed": "drop",
"MediumSpeed": "drop",
"LowPower": "drop"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),
    
       Demo(
        input="What is the average cell width in the low power library ? ",
        source="Lef",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain":"This question should be routed to the LowPower (LP) library because the user wants the average cell width in the low power library. ",
"HighDensity": "drop",
"HighDensityLowLeakage": "drop",
"HighSpeed": "drop",
"LowSpeed": "drop",
"MediumSpeed": "drop",
"LowPower": "Keep"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),
       
       Demo(
        input="What is the cell height in the medium speed library? ",
        source="Lef",
        scl_explain="",
        scl_variant="""
```json
{{
"Explain": "This question should be routed to the MediumSpeed (MS) library because the user wants the cell height in the medium speed library.",
"HighDensity": "drop",
"HighDensityLowLeakage": "drop",
"HighSpeed": "drop",
"LowSpeed": "drop",
"MediumSpeed": "drop",
"LowPower": "Keep"
}}
""",
        query= "",
        desc_str = "",
        fk_str = "",
        tables = """"""
    ).to_dict(),
]
