
"""Creates an instruciton dataset for text-to-SQL and text-to-Cypher fineutning
"""

import os 
import json
import argparse 

import os
import yaml
import argparse

from datasets import load_dataset, DatasetDict, Dataset
from huggingface_hub import login
from transformers import AutoTokenizer


from config.sky130 import View, cell_variant_sky130
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.graph_flow.pdk_flow import PDKGraph
from core.graph_flow.design_flow import DesignGraph
from core.eval.test_set import test_queries_lib, test_queries_lef, test_queries_tlef
from core.database.sql import get_desc, get_table_names, get_fk
from core.utils import get_logger
from sft.model import Model 
from sft.utils import plot_data_lengths


class InstructDataset:

    def __init__(self, json_paths, test_queries, model, tokenizer, shuffle=True, filter_max_seq=True, max_seq_length=4028) -> None:
        self.shuffle = shuffle
        self.model = model 
        self.tokenizer = tokenizer
        model = "gpt-3.5-turbo-0125"
        
        self.config = ChipQueryConfig(
            flow_config= FlowConfigs(
                few_shot=False,
                secure=False,
                decompose_query=False,
                graph_recursion_limit=15,
            ),
            lm_config=LMConfigs(
                router_lm=model,
                selector_lm=model,
                generator_lm=model,
                refiner_lm=model,
                planner_lm=model,
                interpreter_lm=model,
            ),
            db_config=DatabaseConfig(
                partition=False,
                in_mem_db=True,
                load_graph_db=False
            ),
        )
        
        self.pdk_flow = PDKGraph(
            config=self.config 
        )

        self.design_flow = DesignGraph(
            config=self.config
        )

       
        train_dataset = self.create_train_set(json_paths=json_paths)
        test_dataset = self.create_test_set(test_queries)

        train_dataset = train_dataset.map(lambda samples: tokenizer(samples["prompts"]))
        test_dataset = test_dataset.map(lambda samples: tokenizer(samples["prompts"]))

        # if filter_max_seq:
        #     print("Dataset Length before dropping >= max_seq_length: ", len(train_dataset))
        #     train_dataset = train_dataset.filter(lambda example: len(example['input_ids']) <= max_seq_length)
        #     print("Dataset Length after dropping >= max_seq_length: ", len(train_dataset))

    
        self.dataset = DatasetDict({
            'train': train_dataset,
            'test': test_dataset,
        })



    def create_train_set(self, json_paths):
        prompts = []
        for key, path in json_paths.items():
            with open(path, "r") as file:
                data = json.load(file)
                for id, sample in data.items(): 
                    inst_out_pair = self.preprocess(
                        view=key,
                        sample=sample,
                        test=False
                    )

                    prompts.append(inst_out_pair)
        

        train_dataset = Dataset.from_dict({"prompts": prompts})
        train_dataset = train_dataset.shuffle(seed=0)   

        return train_dataset 
    

    def create_test_set(self, test_queries_byview):
        prompts = []
        outputs = [] 

        for key, samples in test_queries_byview.items(): 
            for sample in samples: 
                inst_out_pair = self.preprocess(
                    view=key,
                    sample={
                        "view": key,
                        "question": sample["input"],
                        "op_cond": sample["op_cond"],
                        "techlef_op_cond": sample["op_cond"],
                        "scl_library": sample["scl_variant"],
                        "tables": sample["selected_tables"],
                        "query": sample["ground_truth"][0]
                    },
                    test=True
                )
                
                prompts.append(inst_out_pair)
                outputs.append(sample["ground_truth"])


        test_dataset = Dataset.from_dict({"prompts": prompts, "outputs": outputs})
        return test_dataset 

    
    def preprocess(
        self,
        view: str,
        sample: str,
        test = False
    ):
        if view == 'DEF': 
            input = self.design_flow.generator.prompt.format(
                question=sample["question"], 
                stage=sample["stage"], 
                schema=sample["schema"], 
                relationship=sample["edges"]
            )
        else: 
            if sample["view"] == View.Liberty.value:
                if 'temp_corner' in sample.keys(): 
                    op_cond = f"Temperature: {sample['temp_corner']}, Voltage: {sample['voltage_corner']}" 
                else:
                    op_cond = sample["op_cond"]

            elif sample["view"] == View.TechLef.value: 
                op_cond = sample["techlef_op_cond"]
            else: 
                op_cond = ""

            try: 
                input = self.pdk_flow.generator.prompt.format(
                    input=sample["question"],
                    view=sample["view"],
                    desc_str=get_desc(sample["view"], sample["tables"]),
                    table_info="",
                    # table_info=self.config.db_config.pdk_database.get_table_info(table_names=sample["tables"]), 
                    scl_variant=cell_variant_sky130(sample["scl_library"]),
                    op_cond=op_cond,
                    fk_str =get_fk(sample['view'], sample["tables"]),
                )
            except KeyError: 
                input = self.pdk_flow.generator.prompt.format(
                    input=sample["question"],
                    view=sample["view"],
                    desc_str=get_desc(sample["view"], sample["tables"]),
                    table_info="",
                    # table_info=self.config.db_config.pdk_database.get_table_info(table_names=sample["tables"]), 
                    scl_variant=sample["scl_library"],
                    op_cond=op_cond,
                    fk_str =get_fk(sample['view'], sample["tables"]),
                )


        output = sample["query"]  

        if test: 
            full_prompt = self.apply_template(
                user_prompt=input,
                assistant_answer=""
            )        
        else: 
            full_prompt = self.apply_template(
                user_prompt=input,
                assistant_answer=output
            )

        return full_prompt
    

    def apply_template(self, user_prompt, assistant_answer):
        chat_template = self.model.get_chat_template(
            system_prompt="", 
            user_prompt=user_prompt, 
            assistant_answer=assistant_answer
        )
        
        full_prompt = self.tokenizer.apply_chat_template(
            chat_template, 
            tokenize=False, 
            add_generation_prompt=False
        )
        
        return full_prompt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--techlef', type=str, help="Path to techlef JSON file ", required=False, default="./output/SQL_dataset/SQL_dataset_tlef.json")
    parser.add_argument('--lef', type=str, help="Path to techlef JSON file ", required=False, default="./output/SQL_dataset/SQL_dataset_tlef.json")
    parser.add_argument('--lib', type=str, help="Path to techlef JSON file ", required=False, default="./output/SQL_dataset/SQL_dataset_tlef.json")
    parser.add_argument('--def_file', type=str, help="Path to techlef JSON file ", required=False, default="./output/SQL_dataset/SQL_dataset_tlef.json")
    parser.add_argument('--output_dir', type=str, help="Path to output directory ", required=False, default="./output/sft")
    
    args = parser.parse_args()

    techlef = args.techlef 
    lef = args.lef 
    lib = args.lib 
    def_file = args.def_file 
    output_dir = args.output_dir
    
    os.makedirs(output_dir, exist_ok=True)

    logger = get_logger(os.path.join(output_dir, "dataset.log"))
    
    access_token = os.getenv('HF_ACCESS_TOKEN')
    login(token=access_token)

    json_paths = {
        View.TechLef.value: techlef,
        View.Liberty.value: lib,
        View.Lef.value: lef,
        # "DEF": def_file
    }

    test_queries = {
        View.Liberty.value: test_queries_lib,
        View.TechLef.value: test_queries_tlef,
        View.Lef.value: test_queries_lef
    }

    model_name = "llama3.3:70b"

    model = Model(
        model_name=model_name,
        load_model=False,
    )


    tokenizer = AutoTokenizer.from_pretrained(
        model.model_instruct_ids[model_name], 
        token=access_token, 
    ) 
    
    instruct_dataset = InstructDataset(
        json_paths=json_paths, 
        test_queries=test_queries,
        model=model,
        tokenizer=tokenizer,
        shuffle=True
    )    
    
    logger.info(f"CYAN: Training Prompt: {instruct_dataset.dataset['train']['prompts'][0]}")
    logger.info(f"MAGENTA: Test Prompt: {instruct_dataset.dataset['test']['prompts'][0]}")

    plot_data_lengths(
        tokenized_train_dataset=instruct_dataset.dataset["train"], 
        tokenized_val_dataset=instruct_dataset.dataset["test"], 
        save_path=os.path.join(output_dir, "data_lengths_filtered.png")
    )




if __name__ == "__main__":
    main()