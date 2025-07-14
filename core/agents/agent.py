import os
import sys 
import torch 

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface import HuggingFacePipeline
from langchain_openai.chat_models.base import BaseChatOpenAI
# from unsloth import FastLanguageModel
from peft import  PeftModel

from langchain_core.language_models.llms import LLM
from typing import Optional, List, Any
from pydantic import BaseModel


from sft.cfg.config import combine_cfgs
from sft.model import generate, Model
from sft.utils import parse_answer_llama
from config.sky130 import View, cell_variant_sky130

from dotenv import load_dotenv
load_dotenv()

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
except:
    pass 


class DeepSeek:

    def __init__(self, name) -> None:
        self.deepseek_models = [
            'deepseek-reasoner',
            'deepseek-chat',
        ]
        api_key = os.env.get("DEEPSEEK_API_KEY")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.name = name 


    def call(self, sys_prompt, user_prompt):
        response = self.client.chat.completions.create(
            model=self.name,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False
        )
        output = response.choices[0].message.content
        return output



# class ChipXploreModel: 

#     def __init__(self, model_name) -> None:
#         self.chipxplore_models = [
#             'chipxplore-lef',
#             'chipxplore-tlef',
#             'chipxplore-lib'
#         ]

#         if model_name == "chipxplore-lef":
#             self.adapter = "/oscar/data/sreda/mabdelat/PDQ/output/sft-70b-all/llama3_r64/checkpoint-3450-old"
#         elif model_name == "chipxplore-tlef":
#             self.adapter = "/oscar/data/sreda/mabdelat/PDQ/output/sft-70b-all/llama3_r64/checkpoint-3450-old"
#         elif model_name == "chipxplore-lib":
#             # adapter = "./output/sft-70b-lib-r64-a32/llama3_r64/checkpoint-300"
#             self.adapter = "./output/sft-70b-lib-only/llama3_r64/meta-llama/Llama-3.3-70B-Instruct_finetuned/"
#         else:
#             print("Invalid Model Name")
#             sys.exit(0)
        
#         self.config = combine_cfgs("sft/cfg/experiments/llama3.3_r64.yaml") 
#         self.model, self.tokenizer = FastLanguageModel.from_pretrained(
#             model_name=self.adapter,
#             max_seq_length=self.config.train.max_seq_length,
#             dtype=None,
#             load_in_4bit=self.config.bnb.load_in_4bit,
#         )
#         self.tokenizer.pad_token = self.tokenizer.eos_token # end-of-sequence token
#         self.tokenizer.padding_side = "right" # pad to have max seq length
            
#         self.model.eval()
#         self.model.config.use_cache = False
        
#         FastLanguageModel.for_inference(self.model)
#         self.model_hf = Model(
#             model_name="llama3.3:70b",
#             load_model=False,
#         )
        
#     def invoke(self, args):
#         # prompt = self.preprocess(
#         #     view=args["view"],
#         #     args=args
#         # ) 
#         prompt = self.apply_template(
#             user_prompt=args,
#             assistant_answer=""
#         )     
#         prompts = [prompt]

#         outputs = generate(
#             self.model, 
#             self.tokenizer, 
#             prompts, 
#             do_sample=True, 
#             temperature=0.1, 
#             max_new_tokens=1024, 
#             num_samples=1
#         ) 
    
#         ans = parse_answer_llama(outputs[0])

#         return ans 
    
#     def preprocess(
#         self,
#         view: str,
#         args: str,
#     ):
#         if view == 'DEF': 
#             input = self.design_flow.generator.prompt.format(
#                 question=args["question"], 
#                 stage=args["stage"], 
#                 schema=args["schema"], 
#                 relationship=args["edges"]
#             )
#         else: 
#             if args["view"] == View.Liberty.value:
#                 if 'temp_corner' in args.keys(): 
#                     op_cond = f"Temperature: {args['temp_corner']}, Voltage: {args['voltage_corner']}" 
#                 else:
#                     op_cond = args["op_cond"]

#             elif args["view"] == View.TechLef.value: 
#                 op_cond = args["techlef_op_cond"]
#             else: 
#                 op_cond = ""

#             input = self.pdk_flow.generator.prompt.format(
#                 input=args["question"],
#                 view=args["view"],
#                 desc_str=args["desc_str"],
#                 table_info="",
#                 # table_info=self.config.db_config.pdk_database.get_table_info(table_names=sample["tables"]), 
#                 scl_variant=cell_variant_sky130(args["scl_library"]),
#                 op_cond=op_cond,
#                 fk_str =args["fk_str"],
#             )
    
#         full_prompt = self.apply_template(
#             user_prompt=input,
#             assistant_answer=""
#         )        
      
#         return full_prompt

#     def apply_template(self, user_prompt, assistant_answer):
#         chat_template = self.model_hf.get_chat_template(
#             system_prompt="", 
#             user_prompt=user_prompt, 
#             assistant_answer=assistant_answer
#         )
        
#         full_prompt = self.tokenizer.apply_chat_template(
#             chat_template, 
#             tokenize=False, 
#             add_generation_prompt=False
#         )
        
#         return full_prompt


# class ChipXploreLangChainLLM(LLM,BaseModel):
#     class Config:
#         extra = 'allow'  # allow unknown fields

#     """Wraps a ChipXploreModel so that it can be used as a LangChain LLM."""
#     def __init__(self, chipxplore_model: ChipXploreModel, **kwargs):
#         super().__init__(**kwargs)
#         self.chipxplore_model = chipxplore_model

#     @property
#     def _llm_type(self) -> str:
#         return "chipxplore_llm"

#     def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:


#         result = self.chipxplore_model.invoke(prompt)
       
#         return str(result)
    

class Agent:
    
    def __init__(self, context_winow=5028, output_tokens=1048, quantize=True) -> None:
        self.gpt_models = [
            'gpt-3.5-turbo-0125', 
            'gpt-3.5-turbo', 
            'gpt-4-turbo', 
            'gpt-4-turbo-2024-04-09', 
            'gpt-4o-2024-05-13', 
            'gpt-4o-turbo',
            'gpt-4o-mini-2024-07-18'
        ] 

        self.deepseek_models = [
            'deepseek-reasoner',
            'deepseek-chat'
        ]

        self.llama_models = [
            'llama3.1',
            'llama3.1:70b',
            'llama3.3:70b',
            'llama3.1:8b',
            'llama3.2:8b',
            'llama3.1:8b-instruct-q8_0',
            'llama3.1:8b-instruct-q4_0',
            'llama3:70b-instruct',
            'llama3.1:70b-instruct-q4_K_S',
            'llama3.3:70b',
            'mannix/defog-llama3-sqlcoder-8b',
            'llama3-groq-tool-use:70b',
            'deepseek-r1:70b'
        ]
        
        self.hf_models = [
            # SQL Coder models
            'defog/sqlcoder-7b-2',
            'defog/sqlcoder-70b-alpha',
            'defog/llama-3-sqlcoder-8b',
            # llama3.1 models
            'meta-llama/Meta-Llama-3.1-8B-Instruct',
            'meta-llama/Meta-Llama-3.1-8B',
            'meta-llama/Meta-Llama-3.1-70B-Instruct',
            'meta-llama/Meta-Llama-3.1-70B',
            'nvidia/Llama-3.1-Nemotron-70B-Instruct-HF'
        ]
        
        self.chipxplore_models = [
            'chipxplore-lef',
            'chipxplore-tlef',
            'chipxplore-lib'
        ]

        self.quantize = quantize
        self.context_winow = context_winow
        self.output_tokens = output_tokens
        
        
    def get_model(self, model, temperature=0, structured_output=False):
        if model in self.gpt_models: 
            return ChatOpenAI(
                model=model, 
                temperature=temperature, 
                top_p=0.0000000000000000000001, 
                seed=0
            )

        if model in self.deepseek_models:
            # llm_api_key = os.env.get("DEEPSEEK_API_KEY")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                top_p=0.0000000000000000000001, 
                seed=0,
                max_retries=5,
                openai_api_key="sk-2fd90b2a34064eb2be9f8cbaa4aaf53c", 
                openai_api_base='https://api.deepseek.com',
                max_tokens=5028
            )
        
        if model in self.llama_models:
            # if structured_output: 
            # format = 'json'
            # else:
            #     format = ""
                
            return ChatOllama(
                model=model, 
                temperature=temperature,
                # format=format,
                num_ctx='15028',
                num_predict=1048,
                seed=0,
                # num_gpu=3
            ) 

        if model in self.hf_models: 
            # quantize = '70b' in model
            pipe = self.load_hf_pipeline(
                model_name=model, 
                quantize=self.quantize
            )
            return HuggingFacePipeline(pipeline=pipe)

        if model in self.deepseek_models:
            pass 
        
        if model in self.chipxplore_models:
            chipxplore_model = ChipXploreModel(
                model_name=model
            )
            return ChipXploreLangChainLLM(chipxplore_model)
            # pipe = self.load_chipxplore(model_name=model)
            # return HuggingFacePipeline(pipeline=pipe)
        
        print(f"[Error] Invalid Model Type : {model}")
        sys.exit(1)
    
    
    def load_chipxplore(self, model_name):
        if model_name == "chipxplore-lef":
            adapter = "./output/sft-70b-lef-tlef-r64/llama3_r64/checkpoint-2920"
        elif model_name == "chipxplore-tlef":
            adapter = "./output/sft-70b-lef-tlef-r64/llama3_r64/checkpoint-2920"
        elif model_name == "chipxplore-lib":
            # adapter = "./output/sft-70b-lib-r64-a32/llama3_r64/checkpoint-300"
            adapter = "./output/sft-70b-lib-only/llama3_r64/meta-llama/Llama-3.3-70B-Instruct_finetuned/"
        else:
            print("Invalid Model Name")
            sys.exit(0)

        # model, tokenizer = FastLanguageModel.from_pretrained(
        #     model_name=adapter,
        #     max_seq_length=2828,
        #     dtype=None,
        #     load_in_4bit=True,
        # ) 
        # tokenizer.pad_token = tokenizer.eos_token # end-of-sequence token
        # tokenizer.padding_side = "right" # pad to have max seq length
            
        # model.eval()
        # model.config.use_cache = False
        
        # FastLanguageModel.for_inference(model)

        bnb_4bit_compute_dtype = "float16"
        compute_dtype = getattr(torch, bnb_4bit_compute_dtype)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True, 
            bnb_4bit_quant_type="nf4" ,
            bnb_4bit_compute_dtype=compute_dtype, 
            bnb_4bit_use_double_quant=False, 
        )

        access_token = os.getenv('HF_ACCESS_TOKEN')
        base_model = "meta-llama/Llama-3.3-70B-Instruct"  

        base_model_reload = AutoModelForCausalLM.from_pretrained(
            base_model,
            token=access_token,
            quantization_config=bnb_config,
            device_map="auto",
        )   
        
        tokenizer = AutoTokenizer.from_pretrained(
            base_model, 
            token=access_token, 
            trust_remote_code=True
        )
        
        pipe = pipeline(
            "text-generation",
            model=base_model_reload,
            tokenizer=tokenizer,
            max_new_tokens=1048,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=False,
            temperature=0,
            top_p=None,
        )
    
        pipe.model = PeftModel.from_pretrained(base_model_reload, adapter)

        return pipe 
        
    def load_hf_pipeline(self, model_name, quantize=False):
        
        bnb_config = None 
        if quantize: 
            bnb_config = BitsAndBytesConfig(
                llm_int8_enable_fp32_cpu_offload=True,
                load_in_4bit=True, # Activates 8-bit precision loading
                bnb_4bit_quant_type='nf4', # nf4
                bnb_4bit_compute_dtype=torch.float16, # float16
                bnb_4bit_use_double_quant=True, # False
            )
        
        HUGGINGFACEHUB_API_TOKEN = os.get('HUGGINGFACEHUB_API_TOKEN')
        tokenizer = AutoTokenizer.from_pretrained(model_name, token=HUGGINGFACEHUB_API_TOKEN)

        eos_token_id = tokenizer.eos_token_id
        
        pipe_kwargs = {'eos_token_id': eos_token_id}
    
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="cuda",
            use_cache=True,
            quantization_config=bnb_config,
            token=HUGGINGFACEHUB_API_TOKEN,
            low_cpu_mem_usage=True 
        )
        
        # pipe = pipeline(
        #     "text-generation",
        #     model=model,
        #     tokenizer=tokenizer,
        #     max_new_tokens=1048,
        #     do_sample=True,
        #     temperature=0.1,
        #     top_p=None,
        #     return_full_text=False, # added return_full_text parameter to prevent splitting issues with prompt
        #     num_beams=5, # do beam search with 5 beams for high quality results
        #     kwargs=pipe_kwargs
        # ) 
  
        
        terminators = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=1048,
            eos_token_id=terminators,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=False,
            temperature=0,
            top_p=None,
        )

        return pipe 
    

  