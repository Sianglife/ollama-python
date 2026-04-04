import ollama
import datetime
from CONST import MODELNAME

def get_taipei_time():
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_taipei_time",
            "description": "取得臺北當下的時間",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        }
    }
]

first = ollama.chat(
    model=MODELNAME,
    messages=[
        {"role": "user", "content": "臺北現在幾點?"}
    ],
    tools=TOOLS,
)

if first.message.tool_calls:
    tool_call = first.message.tool_calls[0]
    if tool_call.function.name == 'get_taipei_time':
        taipei_time = get_taipei_time()
        messages = [
            {"role": "user", "content": "臺北現在幾點?"},
            {"role": "tool", "tool_name": "get_taipei_time", "content": taipei_time},
        ]

        second = ollama.chat(
            model=MODELNAME,
            messages=messages,
            tools=TOOLS,
        )

        print(second.message.content)