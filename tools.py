import ollama
from CONST import MODELNAME

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_taipei_time",
            "description": "Get local server time for Taipei.",
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
        {"role": "user", "content": "What time is it in Taipei?"}
    ],
    tools=TOOLS,
)

if first.message.tool_calls:
    tool_call = first.message.tool_calls[0]
    if tool_call.function.name == 'get_taipei_time':
        taipei_time = "2024-06-01 10:00:00"
        messages = [
            {"role": "user", "content": "What time is it in Taipei?"},
            {"role": "tool", "tool_name": "get_taipei_time", "content": taipei_time},
        ]

        second = ollama.chat(
            model=MODELNAME,
            messages=messages,
            tools=TOOLS,
        )

        print(second.message.content)