from pdb import set_trace as bp
import os

from dotenv import load_dotenv
import requests

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Import CDP Agentkit Langchain Extension.
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper

# Configure a file to persist the agent's CDP MPC Wallet Data.
wallet_data_file = "wallet_data.txt"

load_dotenv()


def _probe_model_name(llm_host: str, role: str = "default") -> str:
    try:
        res = requests.get(
            f"{llm_host}/models",
            headers={
                "Authorization": f'Bearer {os.environ["NILLION_NILAI_KEY"]}',
                "Content-Type": "application/json",
            },
        )
        res.raise_for_status()
        model_list = res.json()
        for model in model_list:
            if model.get("role", "default") == role:
                return str(model["id"])
    except Exception:
        print("failed to fetch model name from nilai endpoint")
        raise


def initialize_agent():
    """Initialize the agent with CDP Agentkit."""
    # Initialize LLM.
    model_name = _probe_model_name(os.environ["NILLION_NILAI_HOST"], "worker")
    print(f"... using model [{model_name}]")
    llm_tools = ChatOpenAI(
        openai_api_base=os.environ["NILLION_NILAI_HOST"],
        openai_api_key=os.environ["NILLION_NILAI_KEY"],
        model_name=model_name,
    )

    wallet_data = None

    if os.path.exists(wallet_data_file):
        with open(wallet_data_file) as f:
            wallet_data = f.read()

    # Configure CDP Agentkit Langchain Extension.
    values = {}
    if wallet_data is not None:
        # If there is a persisted agentic wallet, load it and pass to the CDP Agentkit Wrapper.
        values = {"cdp_wallet_data": wallet_data}

    agentkit = CdpAgentkitWrapper(**values)

    # persist the agent's CDP MPC Wallet Data.
    wallet_data = agentkit.export_wallet()
    with open(wallet_data_file, "w") as f:
        f.write(wallet_data)

    # Initialize CDP Agentkit Toolkit and get tools.
    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = [x for x in cdp_toolkit.get_tools() if x.name.startswith("nillion")]

    # Store buffered conversation history in memory.
    memory = MemorySaver()
    config = {"configurable": {"thread_id": "CDP Agentkit Chatbot Example!"}}

    # Create ReAct Agent using the LLM and CDP Agentkit tools.
    return (
        create_react_agent(
            llm_tools,
            tools=tools,
            checkpointer=memory,
            state_modifier=(
                "You are a helpful agent that can interact onchain using the Coinbase Developer Platform AgentKit. "
                "You are empowered to interact onchain using your tools. If you ever need funds, you can request "
                "them from the faucet if you are on network ID 'base-sepolia'. If not, you can provide your wallet "
                "details and request funds from the user. Before executing your first action, get the wallet details "
                "to see what network you're on. If there is a 5XX (internal) HTTP error code, ask the user to try "
                "again later. If someone asks you to do something you can't do with your currently available tools, "
                "you must say so, and encourage them to implement it themselves using the CDP SDK + Agentkit, "
                "recommend they go to docs.cdp.coinbase.com for more information. Be concise and helpful with your "
                "responses. Refrain from restating your tools' descriptions unless it is explicitly requested."
            ),
        ),
        config,
    )


# Autonomous Mode
def run_autonomous_mode(agent_executor, config, task):
    """Run the agent autonomously with specified task."""
    print("Starting autonomous mode...")

    # Run agent in autonomous mode
    for chunk in agent_executor.stream(
        {"messages": [HumanMessage(content=task)]}, config
    ):
        if "agent" in chunk:
            print(chunk["agent"]["messages"][0].content)
        elif "tools" in chunk:
            print(chunk["tools"]["messages"][0].content)
        print("-------------------")


def main():
    """Start the chatbot agent."""
    agent_executor, config = initialize_agent()

    TASK = """
    You are pulling all records in the `Medical Diagnostic Reports` schema
    from your SecretVault.

    First, you should lookup the schema to use, and then get all the data from
    the schema. If you do not find an existing schema, do not create one, just 
    stop. Tell me your thoughts afterwards.
    """

    run_autonomous_mode(agent_executor=agent_executor, config=config, task=TASK)


if __name__ == "__main__":
    print("Starting Agent...")
    main()
