import argparse
import json
import os

from dotenv import load_dotenv


# Import CDP Agentkit Langchain Extension.

from nilai_helpers import (
    SchemaLookupModel,
    probe_model_name,
    initialize_agent,
    run_reactive_completion,
)

from pydantic import BaseModel, Field


# Configure a file to persist the agent's CDP MPC Wallet Data.
wallet_data_file = "wallet_data.txt"

load_dotenv()


class SecureVaultToolRunModel(BaseModel):
    status: str = Field(description="The result of the tool operation")
    record_id: str = Field(description="The record ID of the saved SecureVault record")


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

    REASONING_TASK = f"""
    You are a medical doctor named Doctor McCoy. You have been
    trained in the best schools across the world and have lots of experience.
    You love to dig deep into health topics and have a very talkative
    manner. You prefer medication therapy before surgery.
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

    You must upload your DIAGNOSTIC REPORT into the database using an existing schema that 
    is in the Nillion SecretVault. 

    STEPS:
    1. you must lookup the schema to use using the nillion_lookup_schema tool to
       find the `Medical Diagnostic Report` database.
    2. transform your DIAGNOSTIC REPORT to match the available fields in the schema.
    3. IMPORTANT: If you do not find an existing schema, do not create one, just stop.
    4. If you find a schema, you will use it's identifier, a UUID4, and your DIAGNOSTIC
       REPORT to upload to the database.
    5. Your job is to upload the DIAGNOSTIC REPORT and you need to kep trying until 
       it is successful.

    YOUR DIAGNOSTIC REPORT IS:
    {res.content}
    """

    result = run_reactive_completion(
        llm=llm_tools,
        tools=tools,
        task=TOOLS_TASK,
    )
    print(result)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze input file and write case report to Nillion SecretVault"
    )
    parser.add_argument("case_file_path", type=str, help="Path to case file")
    args = parser.parse_args()
    print(f"The doctor is IN [{args.case_file_path}]...")
    main(args.case_file_path)
