from typing import List

from langchain_core.tools import tool
from langchain_ollama import ChatOllama


@tool
def multiply(x: int, y: int) -> float:
    """Validate user using historical addresses.

    Args:
        user_id (int): the user ID.
        addresses (List[str]): Previous addresses as a list of strings.
    """
    return x*y

print("Heloo")
llm = ChatOllama(
    model="llama3.3:70b",
    temperature=0,
).bind_tools([multiply])

result = llm.invoke(
    "What is 2*3 ?"
)
print(result)
print(result.tool_calls)