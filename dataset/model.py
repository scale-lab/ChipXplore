import os
import re
import sys 
import argparse
from typing import List

import openai 


class GPTModel:

    names = [
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-0125',
        'gpt-4-turbo-2024-04-09',
        'gpt-4o-2024-05-13',
        'gpt-4o-mini-2024-07-18',
        'gpt-4o-mini',
        'gpt-4-turbo'
    ]
 
    def __init__(self, name):
        self.name = name
        api_key = os.environ.get('OPENAI_KEY')
        self.client = openai.OpenAI(api_key=api_key) 

    def generate_chat_template(self, system_prompt: str, user_prompt: str, assistant_answer: str = ""):
        messages = []
        if system_prompt: 
            messages = [{
                'role': 'assistant',
                'content': system_prompt
            }]

        if assistant_answer: 
            messages.append({"role": "assistant", "content": assistant_answer})

        messages.append({'role': 'user', 'content': user_prompt})
        
        return messages

    def message(self, system_prompt, user_prompt, temperature=0.4, num_samples=1):
        answers = []
        prompt = self.generate_chat_template(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        try:
            response = self.client.chat.completions.create(
                model=self.name,
                messages=prompt,
                temperature=temperature,
                n=num_samples,
                seed=0
            )
        
            for choice in response.choices:
                answers.append(choice.message.content)
            return answers
        except openai.OpenAIError as e:
            print(f"OpenAIError: {e}.", flush=True)
            sys.exit(0)


