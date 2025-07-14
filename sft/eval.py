"""Evaluate Fine-tuned model
"""

import os
import sys 
import tqdm
import argparse
from typing import List

import torch 
import numpy as np
from transformers import BitsAndBytesConfig
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from datasets import Dataset 
from peft import  PeftModel
from transformers import set_seed
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from unsloth import FastLanguageModel

from config.sky130 import View 
from sft.utils import parse_answer_llama
from sft.cfg.config import combine_cfgs
from sft.model import Model, generate 
from core.utils import get_logger, parse_sql_from_string
from sft.utils import set_seed, print_trainable_parameters
from sft.data import InstructDataset
from core.eval.test_set import test_queries_lib, test_queries_lef, test_queries_tlef
from core.eval.metrics import compute_execution_acc, compute_ves



def test_model(
    model, 
    tokenizer: AutoTokenizer, 
    dataset: Dataset, 
    temperature: float, 
    num_samples: int = 1, 
    batch_size: int = 16
):
    model.eval()
    model.config.use_cache = True

    print("testing model")

    inputs = []
    answers = []
    
    for i in tqdm.tqdm(range(0, len(dataset), batch_size)):
        batch = dataset[i:i + batch_size]
        prompts = batch['prompts']
        
        outputs = generate(
            model, 
            tokenizer, 
            prompts, 
            do_sample=True, 
            temperature=temperature, 
            max_new_tokens=1024, 
            num_samples=num_samples
        )
        
        batch_responses = []
        for output in outputs: 
            ans = parse_answer_llama(output)
            print(ans)
            batch_responses.append(ans)

        inputs.extend(prompts)
        answers.extend(batch_responses)
        
    return inputs, answers



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, help="Path to config file used for finetuning", required=True)
    parser.add_argument('--adapter', type=str, help="Path to finetuned LoRA adapter or name of the HF adapter.", required=True)
    parser.add_argument('--temperature', type=float, help="Temperature value for LLM generation", default=0.1)
    parser.add_argument('--output_dir', type=str, help="Path to output directory", required=True)
    args = parser.parse_args()

    config_file = args.config
    temperature = args.temperature
    adapter = args.adapter 
    output_dir = args.output_dir

    access_token = os.getenv('HF_ACCESS_TOKEN')
    
    if not access_token:
        logger.info(f"RED: Please set the HF_ACCESS_TOKEN!")
        sys.exit(0)

    os.makedirs(output_dir, exist_ok=True)
    
    config = combine_cfgs(config_file)

    model_name = config.LLM.NAME 
    logfile = os.path.join(output_dir, f"{model_name}")
    logger = get_logger(output=logfile)
    
    set_seed(config.seed)
    
    logger.info(f"CYAN: Temperature set to {temperature}")
    logger.info(f"CYAN: Testing Checkpoint {adapter}")

    base_model = Model.model_instruct_ids[model_name]    
    
    bnb_4bit_compute_dtype = "float16"
    compute_dtype = getattr(torch, bnb_4bit_compute_dtype)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=config.bnb.load_in_4bit, 
        bnb_4bit_quant_type=config.bnb.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype=compute_dtype, 
        bnb_4bit_use_double_quant=config.bnb.bnb_4bit_use_double_quant, 
    )

    # # Load base model
    # base_model_reload = AutoModelForCausalLM.from_pretrained(
    #     base_model,
    #     token=access_token,
    #     quantization_config=bnb_config,
    #     device_map="auto",
    # )

    print("Loading base model")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter,
        max_seq_length=config.train.max_seq_length,
        dtype=None,
        load_in_4bit=config.bnb.load_in_4bit,
    )
    
    
    print("Merging base model with LoRA")
    # merge base model with the finetuned adapter
    # model = PeftModel.from_pretrained(base_model_reload, adapter)
    
    # # # load tokenizer
    # tokenizer = AutoTokenizer.from_pretrained(
    #     base_model, 
    #     token=access_token, 
    #     trust_remote_code=True
    # )

    tokenizer.pad_token = tokenizer.eos_token # end-of-sequence token
    tokenizer.padding_side = "right" # pad to have max seq length
        
    model.eval()
    model.config.use_cache = False
    
    FastLanguageModel.for_inference(model)

    json_paths = {
        View.TechLef.value: config.DATASET.TECHLEF,
        View.Lef.value: config.DATASET.LEF,
        View.Liberty.value: config.DATASET.LIB,
        # "DEF": def_file
    }

    test_queries = {
        # View.Liberty.value: test_queries_lib,
        # View.TechLef.value: test_queries_tlef,
        View.Lef.value: test_queries_lef
    }

    instruct_dataset = InstructDataset(
        model=Model(model_name, load_model=False),
        tokenizer=tokenizer,
        json_paths=json_paths, 
        test_queries=test_queries,
        shuffle=True
    )

    # test finetuned model 
    inputs, answers = test_model(
        model, 
        tokenizer, 
        instruct_dataset.dataset['test'], 
        temperature=config.LLM.TEMP, 
        batch_size=config.test.batch_size, 
        num_samples=config.test.num_samples
    )
    
    predicted_sqls = []
    ground_truth_sqls = []
    targets = instruct_dataset.dataset['test']['outputs']
    for input, answer, target in zip(inputs, answers, targets):
        logger.info(f"CYAN: Input is, {input}")
        logger.info(f"YELLOW: Output is, {answer}")

        predicted_sql = parse_sql_from_string(answer)
        predicted_sqls.append(predicted_sql)
        ground_truth_sqls.append(target)

        logger.info(f"MAGENTA: Final SQL is, {predicted_sql}")
        logger.info(f"GREEN: Target SQL is, {target}")

        execution_accuracy = compute_execution_acc(
            predicted_queries=[predicted_sql], 
            ground_truth_queries=[target],
            database=instruct_dataset.config.db_config.pdk_database
        )

        valid_efficiency_score = compute_ves(
            predicted_queries=[predicted_sql],
            ground_truth=[target],
            database=instruct_dataset.config.db_config.pdk_database,
            num_iters=3
        )

        logger.info(f"YELLOW: EX is, {execution_accuracy}, VES is, {valid_efficiency_score}")


    execution_accuracy = compute_execution_acc(
        predicted_queries=predicted_sqls, 
        ground_truth_queries=ground_truth_sqls,
        database=instruct_dataset.config.db_config.pdk_database
    )

    valid_efficiency_score = compute_ves(
        predicted_queries=predicted_sqls,
        ground_truth=ground_truth_sqls,
        database=instruct_dataset.config.db_config.pdk_database,
        num_iters=3
    )

    logger.info(f"YELLOW: Overall EX is, {execution_accuracy}, Overall VES is, {valid_efficiency_score}")

    
    
  
  


if __name__ == "__main__":
    main()
