import os 
import streamlit as st
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

from core.graph_flow.pdk_flow import PDKGraph
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig

from dotenv import load_dotenv
load_dotenv()

# Setup Application
st.title("ChipXplore")

# Initialize Database and SQLChains

# model = "gpt-4o-mini-2024-07-18"
model = "gpt-4-turbo-2024-04-09"

config = ChipQueryConfig(
    flow_config= FlowConfigs(
        few_shot=True,
        use_in_mem_db=True,
        graph_recursion_limit=10,
        secure=True
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
        load_graph_db=False
    )
)

sql_flow = PDKGraph(
    config=config,
    use_interpreter=True
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept user input
if user_input := st.chat_input("Ask Something about Sky130nm PDK"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            result = sql_flow.forward(
               question=user_input
            )
            st.write(result['final_answer'])
            st.write("Generated SQL:")
            st.write(result['refined_query'])
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": result['final_answer']})

