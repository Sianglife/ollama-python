from openai import OpenAI
import datetime
import json
from loguru import logger
from dotenv import load_dotenv
from CONST import IP, MODELNAME

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    base_url=f"http://{IP}:11434/v1",
    api_key="ollama"
)
def get_taipei_time():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("目前台北時間: {}", now_str)
    return now_str

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

logger.info("=== First Chat START ===")

user_question = "臺北現在幾點?"

first = client.chat.completions.create(
    model=MODELNAME,
    messages=[
        {"role": "user", "content": user_question}
    ],
    tools=TOOLS,
)

message = first.choices[0].message
content = (message.content or "").strip()
logger.info("第一輪回應內容: {}", content)

if content.startswith("[TOOL]"):
    tool_payload = content[len("[TOOL]"):].strip()

    try:
        parsed = json.loads(tool_payload)
    except (json.JSONDecodeError, TypeError):
        logger.error("[TOOL] 後方不是合法 JSON: {}", tool_payload)
        raise

    tool_calls = []
    if isinstance(parsed, dict):
        if "tool_calls" in parsed and isinstance(parsed["tool_calls"], list):
            tool_calls = parsed["tool_calls"]
        elif parsed.get("name"):
            tool_calls = [
                {
                    "id": parsed.get("id", "call_1"),
                    "type": "function",
                    "function": {
                        "name": parsed["name"],
                        "arguments": json.dumps(parsed.get("arguments", {}), ensure_ascii=False),
                    },
                }
            ]

    if not tool_calls:
        logger.error("[TOOL] JSON 中找不到可執行的 tool call")
        raise ValueError("[TOOL] JSON 中找不到可執行的 tool call")

    tool_call = tool_calls[0]
    tool_call_id = tool_call.get("id", "call_1")
    function_name = tool_call.get("function", {}).get("name")
    function_arguments = tool_call.get("function", {}).get("arguments", "{}")

    logger.info("準備呼叫工具: name={}, id={}, args={}", function_name, tool_call_id, function_arguments)

    if function_name == "get_taipei_time":
        _ = json.loads(function_arguments)
        tool_result = get_taipei_time()
    else:
        logger.error("不支援的工具名稱: {}", function_name)
        raise ValueError(f"不支援的工具名稱: {function_name}")

    logger.info("工具執行完成: {}", tool_result)

    assistant_tool_call = {
        "id": tool_call_id,
        "type": "function",
        "function": {
            "name": function_name,
            "arguments": function_arguments,
        },
    }

    messages = [
        {"role": "user", "content": user_question},
        {"role": "assistant", "content": "", "tool_calls": [assistant_tool_call]},
        {"role": "tool", "tool_call_id": tool_call_id, "content": tool_result},
    ]

    second = client.chat.completions.create(
        model=MODELNAME,
        messages=messages,
        tools=TOOLS,
    )

    second_content = (second.choices[0].message.content or "").strip()
    logger.info("第二輪回應內容: {}", second_content)

    if second_content.startswith("[TEXT]"):
        print(second_content[len("[TEXT]"):].strip())
    else:
        print(second_content)

elif content.startswith("[TEXT]"):
    text_output = content[len("[TEXT]"):].strip()
    logger.info("文字回應: {}", text_output)
    print(text_output)

else:
    logger.warning("未偵測到 [TOOL]/[TEXT] prefix，直接輸出原始內容")
    print(content)