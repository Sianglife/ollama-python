from openai import OpenAI
from CONST import IP, MODELNAME


client = OpenAI(
    base_url=f"http://{IP}:11434/v1",
    api_key="ollama"
)

response = client.chat.completions.create(
    model=MODELNAME,
    stream=True,
    messages=[
        {"role": "user", "content": "臺北的捷運有哪些線?"}
    ],
)

for message in response:
    print(message.choices[0].delta.content, end='', flush=True)
