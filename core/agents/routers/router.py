
import os
import argparse

from core.agents.routers.stage_router import StageRouter 
from core.agents.routers.scl_router import SCLRouter
from core.agents.routers.view_router import ViewRouter, View
from core.agents.routers.lib_corner_router import LibCornerRouter
from core.agents.routers.techlef_corner_router import TechLefCornerRouter
from core.eval.test_set import test_queries, test_queries_tlef, test_queries_lib, test_queries_lef
from core.eval.test_graph import test_design
from core.utils import get_logger, parse_temp, parse_voltage

from dotenv import load_dotenv
load_dotenv()


class Router:
    """Encapsulates all router agents
    """
    def __init__(self, model, few_shot=True, temperature=0, llm=None) -> None:
        self.view_router = ViewRouter(
            few_shot=few_shot,
            model=model,
            temperature=temperature,
            llm=llm
        )
        self.scl_router = SCLRouter(
            few_shot=few_shot,
            model=model,
            temperature=temperature,
            llm=llm
        )
        self.techlef_router = TechLefCornerRouter(
            few_shot=few_shot,
            model=model,
            temperature=temperature,
            llm=llm
        )
        self.libcorner_router = LibCornerRouter(
            few_shot=few_shot,
            model=model,
            temperature=temperature,
            llm=llm
        )

    def route(self, query):
        # 1. Route to the relavant standard cell library 
        routed_scl_variant = self.scl_router.route(query)

        # 2. Route to the relevant library view 
        routed_view = self.view_router.route(query)
        
        # 3. Route to the relevant operating condition/corner 
        if routed_view.view == View.TechLef.value:
            techlef_corner = self.techlef_router.route(query=query)
            routed_op_cond = techlef_corner
        elif routed_view.view ==  View.Lef.value:
            routed_op_cond = "'No operating conditions or corners for the LEF view.'"
        elif routed_view.view == View.Liberty.value:
            routed_op_cond = self.libcorner_router.route(query=query)

        return routed_scl_variant, routed_view, routed_op_cond


   
__all__ = [
  'Router'
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/router_eval.log')
    args = parser.parse_args()
    
    model = args.model 
    output = args.output 
    few_shot = not args.wo_fewshot

    logger = get_logger(output)
    
    logger.info(f"YELLOW: \n LLM Agent {model}") 
    logger.info(f"CYAN: Few Shot Set to {few_shot}") 

    # Router agent
    router = Router(
        few_shot=few_shot,
        model=model,
        temperature=0
    )
   
    view_prompt = router.view_router.prompt.format(input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?")
    scl_prompt = router.scl_router.prompt.format(input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?")
    techlef_corner_prompt = router.techlef_router.prompt.format(input="What is the spacing of the met1 routing layer ?")
    libcorner_prompt = router.libcorner_router.prompt.format(input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?")

    logger.info(f"MAGENTA: \n View Router Prompt \n {view_prompt}") 
    logger.info(f"CYAN: \n SCL Router Prompt \n {scl_prompt}") 
    logger.info(f"MAGENTA: \n Corner Router Prompt \n {techlef_corner_prompt}") 
    logger.info(f"CYAN: \n Corner Router Prompt \n {libcorner_prompt}") 

    view_correct = 0
    scl_corect = 0
    
    techlef_corner_correct = 0 
    lib_corner_correct = 0 
    
    for query in test_queries: 
        logger.info(f"CYAN: {query['input']}")

        routed_scl_variant, routed_view, routed_op_cond = router.route(query=query["input"])
        
        # relevant standard cell library
        routed_scl_libraries = routed_scl_variant.get_libraries()
        scl_score = router.scl_router.scl_metric(
            gold=query['scl_variant'], 
            pred=routed_scl_libraries
        )
        scl_corect += scl_score
        
        color = "GREEN" if scl_score else "RED"
        logger.info(f"{color}: \n Cell Library:  {routed_scl_libraries}") 
        logger.info(f"{color}: \n Routed Cell Library Explaination is {routed_scl_variant.Explain}")

        # relevant view
        view_score = router.view_router.view_metric(
            gold=query['view'],
            pred=routed_view.view
        )
        view_correct += view_score
        color = "GREEN" if view_score else "RED"
        logger.info(f"{color}: \n Routed View: {routed_view.view}")
        
        # operating conditions
        op_cond_correct =False 
        if routed_view.view == View.Lef.value:
            op_cond = "'No operating conditions or corners for the LEF view.'"
            op_cond_correct = True 
        elif routed_view.view == View.TechLef.value:
            techlef_corner_score = router.techlef_router.techlef_corner_metric(
                gold=query['op_cond'],
                pred=routed_op_cond.corner
            )
            if techlef_corner_score:
                techlef_corner_correct+=1
                op_cond_correct = True 
            op_cond = f"{routed_op_cond.corner}"
        elif routed_view.view == View.Liberty.value:
            lib_corner_score = router.libcorner_router.lib_corner_metric(
                gold=query['op_cond'],
                pred=routed_op_cond
            )
            if lib_corner_score: 
                lib_corner_correct += 1
                op_cond_correct = True
                
            op_cond = f"Temperature: {routed_op_cond.temperature}, Voltage: {routed_op_cond.voltage}"
          
    
        color = "GREEN" if op_cond_correct  else "RED"
        logger.info(f"{color}: \n Routed Operating Condition: {op_cond}")
        
        if query['view'] != View.Lef.value and routed_view.view != View.Lef.value:
            corner_correct = lib_corner_score if query['view'] == View.Liberty.value else techlef_corner_score
            color = "GREEN" if corner_correct  else "RED"
            try: 
                logger.info(f"{color}:\n Routed Operating Explaination is {routed_op_cond.explain}")
            except:
                logger.info(f"RED:\n Failed to parse operating conditions")
    
    router_accuracy = view_correct / len(test_queries)
    scl_router_accuracy = scl_corect / len(test_queries)
    techlef_corner_acc = techlef_corner_correct / len(test_queries_tlef)
    lib_corner_acc = lib_corner_correct / len(test_queries_lib)
    corner_acc = (techlef_corner_acc + lib_corner_acc) / 2.0

    logger.info(f"BLUE: \n View Router accuracy is {router_accuracy}")
    logger.info(f"BLUE: \n Cell Library Router accuracy is {scl_router_accuracy}")
    logger.info(f"BLUE: \n Corner Router accuracy is {corner_acc}")

    logger.info(f"CYAN: \n Liberty-Corner Router accuracy is {lib_corner_acc}")
    logger.info(f"CYAN: \n TechLef-Corner Router accuracy is {techlef_corner_acc}")
    
    # correct = 0
    # stage_router = StageRouter(
    #     model=model, 
    #     temperature=0
    # )
    
    # for query in test_design: 
    #     logger.info(f"CYAN: {query['input']}")
        
    #     stage = stage_router.route(query=query)
        
    #     routed_stages = stage.get_stages()
        
    #     correct += 1 if set(routed_stages) == set(query["stage"]) else 0
            
    #     color = "GREEN" if set(routed_stages) == set(query["stage"]) else "RED"
    #     logger.info(f"MAGENTA: \n Explaination:  {stage.explain}")
    #     logger.info(f"{color}: \n Stage  is {stage.get_stages()}")

    # stage_accuracy = correct / len(test_design)
    # logger.info(f"CYAN: \n Stage accuracy is {stage_accuracy}")

        

if __name__ == '__main__':
    main()