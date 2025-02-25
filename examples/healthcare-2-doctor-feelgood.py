import argparse
import os
import json

from dotenv import load_dotenv


# Import CDP Agentkit Langchain Extension.

from nilai_helpers import (
    SchemaLookupModel,
    initialize_agent,
    run_reactive_completion,
    secret_vault_save,
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

    REASONING_TASK = f"""
    Your name is Doctor Feelgood. You're the one that makes you feel, alright.
    You are a helpful human physician with an expertise in Internal Medicine.
    You have been asked to help diagnose a patient. Here are all the case
    details.

    INTAKE:
    {json.dumps(data['INTAKE'])}

    CHART:
    {json.dumps(data['CHART'])}

    Form an opinion and suggest a diagnosis. Summarize your reasoning.
    """
    res = llm_reasoning.invoke(REASONING_TASK)

    model_name = probe_model_name(os.environ["NILLION_NILAI_HOST"], "reasoning")
    TOOLS_TASK = f"""
    You are a doctor named Doctor Feelgood working at the {model_name} institution.
    You have already formed an expert opinion and formed a diagnosis of a patients
    condition. This is your DIAGNOSTIC REPORT and this report is found below.

    Simply rephrase the following report into a concise format without losing substance.

    YOUR DIAGNOSTIC REPORT IS:
    {res.content}
    """

    secret_vault_save(str(schema_info[0]), TOOLS_TASK)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze input file and write case report to Nillion SecretVault"
    )
    parser.add_argument("case_file_path", type=str, help="Path to case file")
    args = parser.parse_args()
    print(f"The doctor is IN [{args.case_file_path}]...")
    main(args.case_file_path)
