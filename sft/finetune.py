"""Finetune LLMs on an instruction dataset using LoRA
"""
import os 
import sys
import yaml
import torch
import argparse 
import numpy as np
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model
from trl import SFTTrainer, SFTConfig
from accelerate import Accelerator
from unsloth import FastLanguageModel

from config.sky130 import View 
from core.utils import get_logger, parse_sql_from_string
from sft.model import Model 
from sft.cfg.config import combine_cfgs
from sft.utils import plot_loss
from sft.data import InstructDataset
from utils import set_seed, print_trainable_parameters
from huggingface_hub import login
from core.eval.test_set import test_queries_lib, test_queries_lef, test_queries_tlef
from sft.eval import test_model
from core.eval.metrics import compute_execution_acc, compute_ves

access_token = os.getenv('HF_ACCESS_TOKEN')
login(token=access_token)



def fine_tune_unsloth(
    model_name, 
    dataset, 
    config, 
    output_dir,
    logger,
    checkpoint=None, 
):
   
    # Load base model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=config.train.max_seq_length,
        dtype=None,
        load_in_4bit=config.bnb.load_in_4bit,
    )
    
    print_trainable_parameters(model, logger)
    print(model)

    model = FastLanguageModel.get_peft_model(
        model,
        r=config.lora.lora_r,
        lora_alpha=config.lora.lora_alpha,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing=config.train.gradient_checkpointing,
        random_state=config.seed,
        use_rslora=False,
        loftq_config=None,
    )
    
    print_trainable_parameters(model, logger)
    print(model)
    
    if torch.cuda.device_count() > 1: # If more than 1 GPU
        model.is_parallelizable = True
        model.model_parallel = True
    
    # call model before finetuning 
    # test_model(model, tokenizer, dataset['test'][0:20])
   
    model.config.use_cache = False

    if config.train.gradient_checkpointing: 
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant":False})
    else:
        model.gradient_checkpointing_disable()
    
    training_arguments = SFTConfig(
            per_device_train_batch_size=config.train.batch_size,
            per_device_eval_batch_size=config.train.batch_size,
            gradient_accumulation_steps=config.train.gradient_accumulation_steps, # make finetuing 7 times slower !
            num_train_epochs=config.train.epochs,
            warmup_steps=config.train.warmup_steps,
            dataloader_num_workers=config.train.dataloader_num_workers,
            max_steps=config.train.max_steps,
            learning_rate=config.train.learning_rate,
            lr_scheduler_type=config.train.lr_scheduler_type,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=config.train.logging_steps,
            eval_delay=0,
            logging_strategy=config.train.logging_strategy,
            eval_strategy=config.train.evaluation_strategy,
            save_strategy=config.train.save_strategy,
            save_steps=config.train.save_steps,
            eval_steps=config.train.eval_steps, 
            output_dir=output_dir,
            load_best_model_at_end=config.train.load_best_model_at_end,
            run_name=config.train.run_name,  # name of the W&B run (optional)
            report_to=config.train.report_to,
            gradient_checkpointing=config.train.gradient_checkpointing,  # Leads to reduction in memory at slighly decrease in speed
            # gradient_checkpointing_kwargs={"use_reentrant": True},
            dataset_text_field="prompts",

    )
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        # packing=True,
        # formatting_func=formatting_func,
        args=training_arguments,
        # max_seq_length=config.train.max_seq_length
    )

    # Train model
    if checkpoint: 
        trainer.train(checkpoint)
    else:
        trainer.train()
    
    save_path = os.path.join(output_dir, f"{model_name}_finetuned")
    trainer.model.save_pretrained(save_path)
    
    plot_loss(trainer.state.log_history, os.path.join(output_dir, "loss.png"))

    # test the finetuned model on test set
    FastLanguageModel.for_inference(model)

    return model 




def fine_tune(
    model_name: str, 
    dataset, 
    config, 
    logger,
    checkpoint=None,
    output_dir="./results"
):
   
    # load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, 
        token=access_token, 
        use_fast=config.tokenizer.use_fast,
        trust_remote_code=True
    )
    tokenizer.pad_token = tokenizer.eos_token # end-of-sequence token
    tokenizer.padding_side = config.tokenizer.padding_side # pad to have max seq length

    # Load model in 4-bits and half precision
    bnb_4bit_compute_dtype = "float16"
    compute_dtype = torch.bfloat16
    # getattr(torch, bnb_4bit_compute_dtype)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=config.bnb.load_in_4bit, # Activates 4-bit precision loading
        bnb_4bit_quant_type=config.bnb.bnb_4bit_quant_type, # nf4
        bnb_4bit_compute_dtype=compute_dtype, # float16
        bnb_4bit_use_double_quant=config.bnb.bnb_4bit_use_double_quant, # False
    )

    # Load base model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        token=access_token,
        quantization_config=bnb_config,
        device_map={"": Accelerator().process_index},
        # attn_implementation="flash_attention_2",
        # torch_dtype=torch.float16
    )
    model.config.pretraining_tp = 1

    print_trainable_parameters(model, logger)
    print(model)
    
    # Load LoRA configuration
    peft_config = LoraConfig(
        lora_alpha=config.lora.lora_alpha,
        lora_dropout=config.lora.lora_dropout,
        r=config.lora.lora_r,
        use_dora=config.lora.use_dora,
        bias="none",
        task_type="CAUSAL_LM",
        # target_modules=["q_proj", "k_proj", "v_proj", "o_proj","gate_proj", "up_proj"]
    )

    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, peft_config)

    print_trainable_parameters(model, logger)
    print(model)
    
    if torch.cuda.device_count() > 1: # If more than 1 GPU
        model.is_parallelizable = True
        model.model_parallel = True
    
    # call model before finetuning 
    # test_model(model, tokenizer, dataset['test'][0:20])
   
    model.config.use_cache = False

    if config.train.gradient_checkpointing: 
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant":False})
    else:
        model.gradient_checkpointing_disable()
    
    training_arguments = SFTConfig(
        per_device_train_batch_size=config.train.batch_size,
        per_device_eval_batch_size=config.train.batch_size,
        gradient_accumulation_steps=config.train.gradient_accumulation_steps, # make finetuing 7 times slower !
        num_train_epochs=config.train.epochs,
        warmup_steps=config.train.warmup_steps,
        dataloader_num_workers=config.train.dataloader_num_workers,
        max_steps=config.train.max_steps,
        learning_rate=config.train.learning_rate,
        lr_scheduler_type=config.train.lr_scheduler_type,
        # fp16=not torch.cuda.is_bf16_supported(),
        # bf16=torch.cuda.is_bf16_supported(),
        # fp16=True,
        tf32=True,
        optim="paged_adamw_8bit",
        # fp16=not torch.cuda.is_bf16_supported(),
        # # Set whether to use 16-bit floating-point precision (fp16)
        # bf16=torch.cuda.is_bf16_supported(),
        # Set whether to use Bfloat16
        logging_steps=config.train.logging_steps,
        eval_delay=0,
        logging_strategy=config.train.logging_strategy,
        eval_strategy=config.train.evaluation_strategy,
        save_strategy=config.train.save_strategy,
        save_steps=config.train.save_steps,
        eval_steps=config.train.eval_steps, 
        output_dir=output_dir,
        load_best_model_at_end=config.train.load_best_model_at_end,
        run_name=config.train.run_name,  # name of the W&B run (optional)
        report_to=config.train.report_to,
        gradient_checkpointing=config.train.gradient_checkpointing,  # Leads to reduction in memory at slighly decrease in speed
        # gradient_checkpointing_kwargs={"use_reentrant": True},
        dataset_text_field="prompts",
        max_seq_length=config.train.max_seq_length
    )
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        args=training_arguments,
        peft_config=peft_config,
    )

    # Train model
    if checkpoint: 
        trainer.train(checkpoint)
    else:
        trainer.train()
        
    trainer.model.save_pretrained(os.path.join(output_dir, f"{model_name}_finetuned"))
    
    plot_loss(trainer.state.log_history, os.path.join(output_dir, "loss.png"))

    return model 


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, help="Path to config file for training", required=False, default="sft/cfg/experiments/llama3.3_r64.yaml")
    parser.add_argument('--checkpoint', type=str, help="Resume finetuning from checkpoint", required=False, default=None)
    parser.add_argument('--use_sloth', action='store_const', const=True, help="Use sloth models for faster finetuning", default=True)
    parser.add_argument('--view', type=str, help="View to finetune", default=None)
    parser.add_argument('--run_name', type=str, help="Name of the run", default=None)
    parser.add_argument('--output_dir', type=str, help="Path to output directory ", required=False, default="./output/sft")

    args = parser.parse_args()

    config_file = args.config 
    checkpoint = args.checkpoint
    view = args.view 
    use_sloth = args.use_sloth
    run_name = args.run_name
    output_dir = args.output_dir
    
    config = combine_cfgs(config_file)

    shuffle = config.DATASET.SHUFFLE 
    model_name = config.LLM.NAME 

    output_dir = os.path.join(output_dir, config.train.run_name)
    os.makedirs(output_dir, exist_ok=True)

    logfile = os.path.join(output_dir, f"{model_name}")
    logger = get_logger(output=logfile)
    
    logger.info(f"BLUE: Number of GPUs {torch.cuda.device_count()}")
    logger.info(f"BLUE: Finetuning {model_name}")

    if run_name:
        config.train.run_name = run_name
    
 
    set_seed(config.seed, n_gpu=torch.cuda.device_count())

    with open(os.path.join(output_dir, "config.yaml"), 'w') as f:
        yaml.dump(config, f)


    model = Model(model_name, load_model=False)
    model_id = Model.model_instruct_ids[model_name]
    tokenizer = AutoTokenizer.from_pretrained(
        model.model_instruct_ids[model_name], 
        token=access_token, 
    ) 
    
    tokenizer.pad_token = tokenizer.eos_token # end-of-sequence token
    tokenizer.padding_side = config.tokenizer.padding_side # pad to have max seq length

    if view is None: 
        json_paths = {
            View.TechLef.value: config.DATASET.TECHLEF,
            View.Lef.value: config.DATASET.LEF,
            View.Liberty.value: config.DATASET.LIB,
            # "DEF": def_file
        }

        test_queries = {
            View.Liberty.value: test_queries_lib,
            View.TechLef.value: test_queries_tlef,
            View.Lef.value: test_queries_lef
        }
    elif view == "techlef":
        json_paths = {
            View.TechLef.value: config.DATASET.TECHLEF,
        }
        test_queries = {
            View.TechLef.value: test_queries_tlef,
        } 
    elif view == "lef":
        json_paths = {
            View.Lef.value: config.DATASET.LEF,
        }
        test_queries = {
            View.Lef.value: test_queries_lef
        }  
    elif view == "lib":
        json_paths = {
            View.Liberty.value: config.DATASET.LIB,
        }
        test_queries = {
            View.Liberty.value: test_queries_lib,
        }   
    else:
        print(f"Invalid View Name: {view}")
        sys.exit(0)

    instruct_dataset = InstructDataset(
        model=model,
        tokenizer=tokenizer,
        json_paths=json_paths, 
        test_queries=test_queries,
        shuffle=shuffle
    )

    effective_batch_size = config.train.batch_size*config.train.gradient_accumulation_steps
    logger.info(f"BLUE: Training data length {len(instruct_dataset.dataset['train'])} Testing data length {len(instruct_dataset.dataset['test'])}" )
    logger.info(f"BLUE: Training steps {(len(instruct_dataset.dataset['train'])/effective_batch_size)*config.train.epochs} ")

    if checkpoint:
        logger.info(f"Resuming finetuning from checkpoint {checkpoint}")
    
    # Run finetuning
    if use_sloth:
        model = fine_tune_unsloth(
            model_name=model_id, 
            dataset=instruct_dataset.dataset, 
            config=config, 
            logger=logger,
            checkpoint=checkpoint, 
            output_dir=output_dir
        )
    else:
        model = fine_tune(
            model_name=model_id, 
            dataset=instruct_dataset.dataset, 
            config=config, 
            logger=logger,
            checkpoint=checkpoint, 
            output_dir=output_dir
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
