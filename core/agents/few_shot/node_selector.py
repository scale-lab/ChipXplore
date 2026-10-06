# Copyright (c) 2025, SCALE Lab, Brown University
# All rights reserved.

# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

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