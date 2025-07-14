node_few_shot = [
     
    {
        "input": "What is the total cell count in the design ?",
        "nodes":"""
```json
{{
"Design": "keep",
"Port": "drop",
"Cell": "keep",
"CellInternalPin": "drop",
"Net": "drop",
"Segment": "drop"
}}
```
""",    
    },

    {
        "input": "What is the number of nets in the design ?",
        "nodes":"""
```json
{{
"Design": "keep",
"Port": "drop",
"Cell": "drop",
"CellInternalPin": "drop",
"Net": "keep",
"Segment": "drop"
}}
```
""",    
    },

]