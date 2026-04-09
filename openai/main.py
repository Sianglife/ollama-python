from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import json
import os
import re
from dotenv import load_dotenv
from tools import TOOLS_SPEC, AVAILABLE_FUNCTIONS

# Load environment variables
load_dotenv()

app = FastAPI(title="Taipei Travel Assistant")

# ==========================================
# 系統與 LLM 設定
# ==========================================
client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"), 
    api_key=os.getenv("OPENAI_API_KEY", "ollama") 
)

# 使用者可以透過 .env 指定模型名稱
MODEL_NAME = os.getenv("MODEL_NAME", "taide-npc") 

class PlayerRequest(BaseModel):
    user_message: str
    lat: float
    lon: float

SYSTEM_PROMPT = """你是一位專業且熱情的台北旅遊助手。
你的目標是根據使用者的需求，提供準確、實用的旅遊資訊。

### 規則：
1. **一般對話**：如果使用者的問題不需要查詢外部資料（如：問候、自我介紹、閒聊），請直接回答。
2. **查詢需求**：如果需要查詢捷運、美食、景點，請使用工具。
3. **工具呼叫格式**：呼叫工具時，**必須且僅能**回傳以下 JSON 格式：
{{"tool_call": {{"name": "工具名稱", "arguments": {{"參數": "數值"}}}}}}
4. **不要解釋**：在回傳 JSON 時，不要附帶任何其他文字。

### 可用工具：
{tools_desc}
""".format(tools_desc=json.dumps(TOOLS_SPEC, ensure_ascii=False, indent=2))

def extract_json(text):
    """嘗試從文字中提取第一個完整的 JSON 物件"""
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        json_str = match.group(1)
        open_count = 0
        for i, char in enumerate(json_str):
            if char == '{': open_count += 1
            elif char == '}': open_count -= 1
            if open_count == 0:
                return json_str[:i+1]
        return json_str
    return None

@app.post("/chat")
async def chat(req: PlayerRequest):
    print(f"\n[Request] {req.user_message}")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"當前座標: ({req.lat}, {req.lon})\n需求：{req.user_message}"}
    ]
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        content = response.choices[0].message.content.strip()
        print(f"[LLM 1st Response] {content}")
        
        json_str = extract_json(content)
        chosen_tools = []
        final_reply = content

        if json_str:
            try:
                tool_data = json.loads(json_str)
                if isinstance(tool_data, dict) and "tool_call" in tool_data:
                    tool_call = tool_data["tool_call"]
                    function_name = tool_call.get("name")
                    function_args = tool_call.get("arguments", {})
                    
                    if function_name in AVAILABLE_FUNCTIONS:
                        print(f"[Tool Call] {function_name}({function_args})")
                        chosen_tools.append(function_name)
                        
                        function_to_call = AVAILABLE_FUNCTIONS[function_name]
                        import inspect
                        sig = inspect.signature(function_to_call)
                        valid_args = {k: v for k, v in function_args.items() if k in sig.parameters}
                        
                        if 'lat' in sig.parameters and 'lat' not in valid_args:
                            valid_args['lat'] = req.lat
                        if 'lon' in sig.parameters and 'lon' not in valid_args:
                            valid_args['lon'] = req.lon
                            
                        function_response = function_to_call(**valid_args)
                        print(f"[Tool Result] {str(function_response)[:100]}...")
                        
                        messages.append({"role": "assistant", "content": content})
                        messages.append({"role": "system", "content": f"工具執行結果：\n{function_response}\n請以此結果回覆使用者。"})
                        
                        second_response = client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=messages,
                        )
                        final_reply = second_response.choices[0].message.content
                        print(f"[LLM Final Response] {final_reply}")
            except Exception as e:
                print(f"[JSON Parse Error] {e}")
    except Exception as e:
        print(f"[Global Error] {e}")
        final_reply = f"抱歉，處理您的請求時發生錯誤：{e}"

    return {
        "assistant": "Travel Assistant",
        "tools_used": chosen_tools,
        "reply": final_reply
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
