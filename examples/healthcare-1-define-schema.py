from dotenv import load_dotenv


# Import CDP Agentkit Langchain Extension.

from nilai_helpers import (
    initialize_agent,
    run_reactive_completion,
)

# Configure a file to persist the agent's CDP MPC Wallet Data.
wallet_data_file = "wallet_data.txt"

load_dotenv()


def main():
    _llm_reasoning, llm_tools, tools = initialize_agent()

    TASK = """
    Create a basic schema in the SecretVault so that I can track patient name, doctor name, institution
    name, a medical diagnosis, and a reasoning summary. All of these fields should be secret. Call the 
    schema `Medical Diagnostic Report`
    """

    run_reactive_completion(
        llm=llm_tools,
        tools=tools,
        task=TASK,
    )


if __name__ == "__main__":
    print("Starting Agent...")
    main()
