import ollama
from CONST import MODELNAME

response = ollama.chat(
    model=MODELNAME,
    stream=True,
    messages=[
        {"role": "user", "content": "臺北的捷運有哪些線?"}
    ],
)

for message in response:
    print(message['message']['content'], end='', flush=True)
