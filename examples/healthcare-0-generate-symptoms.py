from dotenv import load_dotenv
import os
from huggingface_hub import InferenceClient

load_dotenv()

HUGGINGFACE_API_KEY = os.environ["HUGGINGFACE_API_KEY"]
PROMPT = """
You are a primary care physician with over twenty years of practice, specializing
in internal medicine and family care.

You are analyzing an adult human with a common midwest American lifestyle. Assume 
all personal details and background befitting this role. This person is your patient
who is suffering from an oft misdiagnosed disease. This condition does express many 
observable symptoms and they can easily be overlooked for a more common conditions. 
The symptoms might be external or internal or a combination of both. You know the
root cause.

You are to create a JSON friendly structure of creative information as specified in
the following. Obey the RULES for output.

Generate a long and creative narriative of your subject that appears like an intake 
sheet for a primary care physician's office. Include vitals, demographics, and a 
listing of the chief complaints related to this condition. This will be in the 
"INTAKE" section.

Generate a creative and detailed symptomology analysis that any nurse practioner, 
or other family doctor, would discover over many visits. Include exhaustive chart 
details such as labs, scans and other findings in the most detailed method possible; 
ensure that the record follows typical EHR standards. This will be the "CHART" section.

Notate the actual root cause with no detail associated to the cause. This will be the 
"CAUSE" section.

EXAMPLE STRUCTURE:
{
    "INTAKE": {
    ...
    },
    "CHART": {
    ...
    },
    "CAUSE": "example disease"
}

OUTPUT RULES:
- Only output the final JSON structure. Do not include reasoning, any markdown, commentry or 
  styling to the output. It should be a valid JSON string only.
- Do not include any markdown in the output.
- Do not include any formulated diagnostic hints or comments in the CHART or INTAKE.

"""



def main():

    messages = [{"role": "user", "content": PROMPT}]

    client = InferenceClient(    provider="together",api_key=HUGGINGFACE_API_KEY)


    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1", 
        messages=messages, 
        max_tokens=500
    )
    print(completion.choices[0].message)

    """
    stream = client.chat.completions.create(
        model="google/gemma-2-2b-it", messages=messages, max_tokens=500, stream=True
    )

    result = "".join([chunk.choices[0].delta.content for chunk in stream])
    print(result)
    """


if __name__ == "__main__":
    print("Starting Agent...")
    main()
    print("COMPLETE")
