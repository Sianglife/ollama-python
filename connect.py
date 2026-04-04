import ollama
from CONST import MODELNAME

response = ollama.chat(
    model=MODELNAME,
    stream=True,
    messages=[
        {"role": "user", "content": "What time is it in Taipei?"}
    ],
)

for message in response:
    print(message['message']['content'], end='', flush=True)
