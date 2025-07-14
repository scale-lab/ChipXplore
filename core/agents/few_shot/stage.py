stage_few_shot = [
    
    {
        "input": "What is the total cell count after the routing stage ?",
        "explain": "The question is asking about the number of cells after routing, so I will route it to the routing stage",
        "stage":"""
```json
{{
    "explain": "The question is explicitly asking about the number of cells after routing, so I will route it to the routing stage",
    "floorplan": "drop",
    "placement": "drop",
    "cts": "drop",
    "routing": "keep"
}}
```

""",
            
    },
    {
        "input": "Compare the number of cells between the cts and routing stages",
        "stage":"""
```json
{{
    "explain": "This question explicitly asks to compare information from the cts and routing stages, so I will route it to both the cts and routing stages.",
    "floorplan": "drop",
    "placement": "drop",
    "cts": "keep",
    "routing": "keep"
}}
```

""",

    },
    {
        "input": "How many output pins does the design have ?",
        "stage":"""
```json
{{
    "explain": "This question didn't explicitly mention a stage. Therefore, since the routing stage contains the final design information, including updates from all previous stages, we'll route to the routing stage for the most up-to-date information.",
    "floorplan": "drop",
    "placement": "drop",
    "cts": "drop",
    "routing": "keep"
}}
```

""",
    },
    {
        "input": "What is the structure of the clock tree?",
        "stage":"""
```json
{{
        "explain": "This question didn't explicitly mention a stage. Therefore, since the routing stage contains the final design information, including updates from all previous stages, we'll route to the routing stage for the most up-to-date information.",
        "floorplan": "drop",
        "placement": "drop",
        "cts": "drop",
        "routing": "keep"
}}
```

"""
    },
    {
        "input": "Compare the congestion levels across all stages of the design process.",
          "stage":"""
```json
{{
    "explain": "This question explicitly asks to compare information across all stages of the design process. Therefore, we need to keep all stages to provide a comprehensive comparison.",
    "floorplan": "keep",
    "placement": "keep",
    "cts": "keep",
    "routing": "keep"
}}
```

"""
    }
       
]