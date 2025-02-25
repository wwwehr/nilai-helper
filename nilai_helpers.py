import os
import requests

from dotenv import load_dotenv

import json
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage


from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper

from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Union

StructuredResponseSchema = Union[dict, type[BaseModel]]


class SchemaLookupModel(BaseModel):
    schema_definition: str = Field(description="The schema serialized to a string")


# Configure a file to persist the agent's CDP MPC Wallet Data.
wallet_data_file = "wallet_data.txt"

load_dotenv()


def probe_model_name(llm_host: str, role: str = "default") -> str:
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

    llm_reasoning = ChatOpenAI(
        openai_api_base=os.environ["NILLION_NILAI_HOST"],
        openai_api_key=os.environ["NILLION_NILAI_KEY"],
        model_name=probe_model_name(os.environ["NILLION_NILAI_HOST"], "reasoning"),
    )

    llm_tools = ChatOpenAI(
        openai_api_base=os.environ["NILLION_NILAI_HOST"],
        openai_api_key=os.environ["NILLION_NILAI_KEY"],
        model_name=probe_model_name(os.environ["NILLION_NILAI_HOST"], "worker"),
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

    return (
        llm_reasoning,
        llm_tools,
        tools,
    )


# Autonomous Mode
def run_reactive_completion(
    llm,
    tools,
    task: str,
    response_format: StructuredResponseSchema | None = None,
    config: dict = {},
):
    """Run the agent autonomously."""
    print("Starting autonomous mode...")

    config = {"configurable": {"thread_id": str(uuid4())}, **config}

    agent_executor = create_react_agent(
        llm, tools=tools, checkpointer=MemorySaver(), response_format=response_format
    )

    last_chunk = {}
    for chunk in agent_executor.stream(
        {"messages": [HumanMessage(content=task)]}, config, stream_mode="values"
    ):
        last_chunk = chunk

    res = {}
    for msg in last_chunk.get("messages", []):
        if len(tools) and isinstance(msg, ToolMessage):
            res["tool"] = msg.content
        elif isinstance(msg, AIMessage):
            res["ai"] = msg.content
        elif isinstance(msg, BaseMessage):
            res["base"] = msg.content
        elif isinstance(msg, SystemMessage):
            res["sys"] = msg.content

    if len(tools):
        if "tool" not in res or not len(res["tool"]):
            return None
        try:
            return json.loads(str(res["tool"]))
        except Exception:
            # ignore json load failure
            return res["tool"]
    else:
        try:
            return json.loads(str(res["ai"]))
        except Exception:
            # ignore json load failure
            return res["ai"]


def invoke_with_secret_vault_and_save(
    model_role: str, schema_uuid: str, task: str, query_filter: dict = {}
):
    # Send POST request directly to nilai endpoint
    chat_completions_url = os.environ["NILLION_NILAI_HOST"] + "/chat/completions"
    tester = requests.post(
        chat_completions_url,
        headers={
            "Authorization": f'Bearer {os.environ["NILLION_NILAI_KEY"]}',
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=3600,
        json={
            "model": probe_model_name(os.environ["NILLION_NILAI_HOST"], model_role),
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": task},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
            "stream": False,
            "secret_vault": {  # secure key migration
                "org_did": os.environ["NILLION_ORG_ID"],
                "secret_key": os.environ["NILLION_SECRET_KEY"],
                "inject_from": schema_uuid,
                "filter": query_filter,
                "save_to": schema_uuid,
            },
        },
    )

    print(json.dumps(tester.json(), indent=4))


def secret_vault_save(schema_uuid: str, task: str):
    # Send POST request directly to nilai endpoint
    chat_completions_url = os.environ["NILLION_NILAI_HOST"] + "/chat/completions"
    tester = requests.post(
        chat_completions_url,
        headers={
            "Authorization": f'Bearer {os.environ["NILLION_NILAI_KEY"]}',
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=3600,
        json={
            "model": probe_model_name(os.environ["NILLION_NILAI_HOST"], "worker"),
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": task},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
            "stream": False,
            "secret_vault": {  # secure key migration
                "org_did": os.environ["NILLION_ORG_ID"],
                "secret_key": os.environ["NILLION_SECRET_KEY"],
                "save_to": schema_uuid,
            },
        },
    )

    print(json.dumps(tester.json(), indent=4))


def invoke_with_secret_vault(
    model_role: str, schema_uuid: str, task: str, query_filter: dict = {}
):
    # Send POST request directly to nilai endpoint
    chat_completions_url = os.environ["NILLION_NILAI_HOST"] + "/chat/completions"
    tester = requests.post(
        chat_completions_url,
        headers={
            "Authorization": f'Bearer {os.environ["NILLION_NILAI_KEY"]}',
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=3600,
        json={
            "model": probe_model_name(os.environ["NILLION_NILAI_HOST"], model_role),
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": task},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
            "stream": False,
            "secret_vault": {  # secure key migration
                "org_did": os.environ["NILLION_ORG_ID"],
                "secret_key": os.environ["NILLION_SECRET_KEY"],
                "inject_from": schema_uuid,
                "filter": query_filter,
            },
        },
    )

    print(json.dumps(tester.json(), indent=4))
