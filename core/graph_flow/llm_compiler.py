class LLMCompilerPlanner():

    def __init__(self, model, few_shot, temperature, pdk_database, design_database) -> None:

        # PDK and Design Subgraphs        
        pdk_subgraph = PDKGraph(
            model=model,
            database=pdk_database,
            few_shot=few_shot,
            temperature=temperature
        )
        
        design_subgraph = DesignGraph(
            model=model,
            database=design_database,
            few_shot=few_shot,
            temperature=temperature 
        )

        pdk_query = StructuredTool.from_function(
            name="pdk_query",
            func = pdk_subgraph.forward,
            description=_PDK_QUERY_DESCR,
        )

        design_query = StructuredTool.from_function(
            name="design_query",
            func=design_subgraph.forward,
            description=_DESIGN_QUERY_DESCR
        )

        tools = [pdk_query, design_query]


    def forward(self, question):
        pass 

