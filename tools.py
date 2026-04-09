from openai import OpenAI
import datetime
import os
from dotenv import load_dotenv
from CONST import MODELNAME

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama")
)

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

first = client.chat.completions.create(
    model=MODELNAME,
    messages=[
        {"role": "user", "content": "臺北現在幾點?"}
    ],
    tools=TOOLS,
)

print(first.choices[0].message)

if first.choices[0].message.tool_calls:
    tool_call = first.choices[0].message.tool_calls[0]
    if tool_call.function.name == 'get_taipei_time':
        taipei_time = get_taipei_time()
        messages = [
            {"role": "user", "content": "臺北現在幾點?"},
            {"role": "assistant", "content": "", "tool_calls": [tool_call]},
            {"role": "tool", "tool_call_id": tool_call.id, "content": taipei_time},
        ]

        second = client.chat.completions.create(
            model=MODELNAME,
            messages=messages,
            tools=TOOLS,
        )

        print(second.choices[0].message.content)