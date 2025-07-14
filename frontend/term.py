import os 
import sys 
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.runner import ChipQueryRunner 

from dotenv import load_dotenv
load_dotenv()


# ANSI color codes
COLOR_USER = "\033[92m"      # Green
COLOR_ASSISTANT = "\033[94m" # Blue
COLOR_SYSTEM = "\033[93m"    # Yellow
COLOR_RESET = "\033[0m"      # Reset to default color


def main():

    # model = "gpt-4o-mini-2024-07-18"
    model = "gpt-4-turbo-2024-04-09"

    config = ChipQueryConfig(
        flow_config= FlowConfigs(
            few_shot=True,
            use_in_mem_db=True,
            graph_recursion_limit=10,
            secure=False
        ),
        lm_config=LMConfigs(
            router_lm=model,
            selector_lm=model,
            generator_lm=model,
            refiner_lm=model,
            planner_lm=model,
            interpreter_lm="gpt-3.5-turbo-0125",
            temperature=0
        ),
        db_config=DatabaseConfig(
            partition=False,
            in_mem_db=True,
            load_graph_db=True,
        )
    )
    
    runner = ChipQueryRunner(
        config=config,
    )
    
    print(f"{COLOR_SYSTEM}Welcome to the PDKQuery shell! Type '\\bye' to exit.{COLOR_RESET}")
    conversation_history = []
    while True:
        try:
            user_input = input(f"{COLOR_USER}You >> {COLOR_RESET} ").strip()
            if user_input.lower() == "\\bye":
                print(f"{COLOR_SYSTEM}Goodbye!{COLOR_RESET}")
                break

            if not user_input:
                continue

            result = runner.forward(
                question=user_input,
            )

            conversation_history.append({"role": "assistant", "content": result['final_answer']})
            print(f"{COLOR_ASSISTANT}Assistant:{COLOR_RESET} {result['final_answer']}")
            print(f"{COLOR_ASSISTANT}Assistant:{COLOR_RESET} {result['query']}")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{COLOR_SYSTEM}Exiting...{COLOR_RESET}")
            break
        except Exception as e:
            print(f"{COLOR_SYSTEM}Error:{COLOR_RESET} {e}", file=sys.stderr)
            continue


if __name__ == "__main__":
    main()
