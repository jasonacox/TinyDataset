import os
import openai
import json

MAXTOKENS = 1000
TEMPERATURE = 0.5

base_url = os.getenv("LLM_API_BASE_URL", "http://localhost:8000/v1")
api_key = os.getenv("LLM_API_KEY", "sk-3-laws-safe")  # If required
llm_model = os.getenv("LLM_MODEL", "llama")

llm = openai.OpenAI(api_key=api_key, base_url=base_url)
llm.models.list()  # List all models

def generate_facts(text):
    # Have LLM extract facts from the provided text
    response = llm.chat.completions.create(
        model=llm_model,
        max_tokens=MAXTOKENS,
        stream=False,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": "Extract facts from the following text. Do no include commentary about the article. List one fact per line."},
            {"role": "user", "content": text}
        ]
    )
    data = response.choices[0].message.content.strip() 
    print(f"Response: {data}")
    # Extract each fact - one per line
    facts = data.split("\n")
    return facts


def generate_qa(fact):
    response = llm.chat.completions.create(
        model=llm_model,
        max_tokens=MAXTOKENS,
        stream=False,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": "Generate 1-5 question and answer pairs about the following fact. Use a double-quoted string JSON format with keys \"question\" and \"answer\"."},
            {"role": "user", "content": fact}
        ]
    )
    data = response.choices[0].message.content.strip()
    print(f"Response: {data}")
    # Find the JSON data in the response
    start = data.find("[")
    end = data.find("]")
    qa_pairs = data[start:end + 1]
    print(qa_pairs)
    if not qa_pairs:
        r = []
    if qa_pairs.startswith("[{") and qa_pairs.endswith("}]"):
        try:
            r = json.loads(qa_pairs)
        except json.JSONDecodeError:
            print("Error decoding JSON data")
            r = []

