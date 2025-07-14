### Run Finetuning

python sft/finetune.py --config sft/cfg/experiments/llama3.3_r64.yaml --output_dir ./output/sft-70b-lib-r64/

python sft/finetune.py --config sft/cfg/experiments/llama3.3_r64.yaml --output_dir ./output/sft-70b-lib-r128/

## Run Inference
/oscar/data/sreda/mabdelat/PDQ/

python sft/eval.py --config sft/cfg/experiments/llama3.3_r64.yaml --adapter ./output/sft-70b-lib-r64-a32/llama3_r64/checkpoint-300 --output_dir ./output/sft-70b-lib-r64-a32/

python sft/eval.py --config sft/cfg/experiments/llama3.3_r64.yaml --adapter ./output/sft-70b-lib-r64-a64/llama3_r64/checkpoint-300 --output_dir ./output/sft-70b-lib-r64-64/

python sft/eval.py --config sft/cfg/experiments/llama3.3_r64.yaml --adapter ./output/sft-70b-lib-r64/llama3_r64/checkpoint-710 --output_dir ./output/sft-70b-lib-r64/llama3_r64/checkpoint-710


python sft/eval.py --config sft/cfg/experiments/llama3.3_r64.yaml --adapter ./output/sft-70b-lib-only/llama3_r64/checkpoint-660 --output_dir ./output/sft-70b-lib-only/llama3_r64/checkpoint-660
