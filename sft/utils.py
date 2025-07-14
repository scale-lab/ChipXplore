import re 
import torch
import numpy as np
import matplotlib.pyplot as plt


def plot_data_lengths(tokenized_train_dataset, tokenized_val_dataset, save_path):
    lengths = [len(x['input_ids']) for x in tokenized_train_dataset]
    lengths += [len(x['input_ids']) for x in tokenized_val_dataset]
    print(len(lengths))

    # Plotting the histogram
    plt.figure(figsize=(10, 6))
    plt.hist(lengths, bins=50, alpha=0.7, color='blue')
    plt.xlabel('Length of input_ids')
    plt.ylabel('Frequency')
    plt.title('Distribution of Lengths of input_ids')
    # plt.xlim([0, 1500])
    plt.savefig(save_path)
    plt.cla()
    plt.close()


def plot_loss(log_history, save_path):
    train_loss = []
    valid_loss = []
    for element in log_history:
        if "loss" in element.keys():
            loss = element["loss"]
            train_loss.append(loss)
        elif "eval_loss" in element.keys():
            loss = element["eval_loss"]
            valid_loss.append(loss)
            
    plt.plot(np.arange(0, len(train_loss)), train_loss, marker = 'o', label='Train Loss')
    plt.plot(np.arange(0, len(valid_loss)), valid_loss, marker = 'o', label='Valid Loss')
    plt.legend()
    plt.xlabel('Steps')
    plt.ylabel('Loss')
    plt.savefig(save_path) 
    plt.cla()
    plt.close()



def print_trainable_parameters(model, logger):
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    logger.info(f"CYAN: trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param}")


def set_seed(seed, n_gpu=1):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if n_gpu > 0:
        torch.cuda.manual_seed_all(seed)


def parse_answer_llama(answer):
    pattern = r'(?:.*assistant)([\s\S]*)'
    match = re.findall(pattern, answer, re.DOTALL)  
    if match:
        result = match[-1]
    else:
        result = None
    return result
