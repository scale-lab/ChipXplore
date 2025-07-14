
techlef_corner_router_few_shot = [
    {
        "input": "What is the width of the met1 layer ?",
        "explain": "The question is asking about the width of the met1 layer, since user did not specifiy a specific corner, I will route it to the nom corner",
        "corner": "['nom']"
    },
    {
        "input": "What is resistance per square unit of the met2 layer in the max corner ?",
        "explain": "The question is asking about the resistance per square of the met2 layer in the max corner, since the user specifices a specific corner which is the max corner,  I will route it to the max corner.",
        "corner": "['max']"
    },
    {
        "input": "What is resistance per square unit of the met2 layer in the min corner ?",
        "explain": "The question is asking about the resistance per square unit of the met2 layer in the min corner, since the user specifices a specific corner which is the min corner, I will route it to the min corner.",
        "corner": "['min']"
    },
    {
        "input": "What is resistance per square unit of the met2 layer in the min and max corner ?",
        "explain": "The question is asking about the resistance per square unit of the met2 layer in the min and max corners, since the user specifices  specific corners which are the min corner and the max corner, I will route it to the min and max corners.",
        "corner": "['min', 'max']"
    },
    {
        "input": "What is the met2 layer resistance per square unit in each corner ?",
        "explain": "The question is asking about the resistance per square unit of the met2 layer in each corner, since the user wants the information in each corner, I will route it to all corners: min, nom, and max",
        "corner": "['min', 'nom', 'max']"
    },
]

lib_corner_few_shot = [
    {
        "input": "What is the area of the sky130_fd_sc_hd__and2_1 cell",
        "explain": "The user did not specify operating conditions, so I will route this to the typical corner with temperature of 25 and voltage of 1.8",
        "temperature": "25.0",
        "voltage": "1.8"
    },
    {
        "input": "What is the propagation delay of the sky130_fd_sc_hd__and2_1 cell under operating conditions with temperature value of 100 and voltage 1.65 ? ",
        "explain": "The user wants the propagation delay of the sky130_fd_sc_hd__and2_1 at a tempertature of 100 and voltage of 1.65, so I will route this to the corner with temperature of 100 and voltage 1.65.",
        "temperature": "100",
        "voltage": "1.65"
    },
    {
        "input": "What is the leakage power of the sky130_fd_sc_hd__and2_1 cell",
        "explain": "The user did not specify operating conditions, so I will route this to the typical corner with temperature of 25 and voltage of 1.8",
        "temperature": "25.0",
        "voltage": "1.8"
    },
    {
        "input": "How many cells are in the high density library ? ",
        "explain": "The user did not specify operating conditions, so I will route this to the typical corner with temperature of 25 and voltage of 1.8",
        "temperature": "25.0",
        "voltage": "1.8"
    },
]