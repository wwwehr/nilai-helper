import argparse
import os
import json

from dotenv import load_dotenv


# Import CDP Agentkit Langchain Extension.

from nilai_helpers import (
    SchemaLookupModel,
    initialize_agent,
    run_reactive_completion,
    invoke_with_secret_vault_and_save,
    probe_model_name,
)


# Configure a file to persist the agent's CDP MPC Wallet Data.
wallet_data_file = "wallet_data.txt"

load_dotenv()


def main(case_file_path: str) -> bool:
    """Start the chatbot agent."""
    try:
        with open(case_file_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {case_file_path} not found")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}")

    llm_reasoning, llm_tools, tools = initialize_agent()

    schema_info = run_reactive_completion(
        llm=llm_tools,
        tools=tools,
        task="find the `Medical Diagnostic Report` database. Only return the schema.",
        response_format=SchemaLookupModel,
    )
    if schema_info is None:
        raise Exception("can't find schema")

    model_name = probe_model_name(os.environ["NILLION_NILAI_HOST"], "reasoning")
    REASONING_TASK = f"""
    You are a doctor named Doctor Drew working at the {model_name} institution.
    You are a physician, but also a celebrity personality. You have vast human 
    relationship experience and have a great sense of humor.
    You have been asked to help diagnose a patient. Here are all the case
    details.

    INTAKE:
    {json.dumps(data['INTAKE'])}

    CHART:
    {json.dumps(data['CHART'])}

    You must consider the diagnosis from two colleagues below. 

    Your task is to form an opinion and suggest a diagnosis.

    Tell me the patient name, your doctor name, institution name, your medical
    diagnosis, and a short reasoning summary.

    """

    _res = invoke_with_secret_vault_and_save(
        "reasoning",
        schema_info[0],
        REASONING_TASK,
        {
            "_id": {
                "$in": [
                    "6e214b90-ea31-4d29-ae57-68af5f2cdc86",
                    "688a3184-c2d7-4aed-ab2f-4d376a9b6a0d",
                ]
            }
        },
    )
    print(_res)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze input file and write case report to Nillion SecretVault"
    )
    parser.add_argument("case_file_path", type=str, help="Path to case file")
    args = parser.parse_args()
    print(f"The doctor is IN [{args.case_file_path}]...")
    main(args.case_file_path)
