import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_chat(user_message, lat=25.0477, lon=121.5170):
    print(f"\n--- 測試對話: '{user_message}' ---")
    url = f"{BASE_URL}/chat"
    payload = {
        "user_message": user_message,
        "lat": lat,
        "lon": lon
    }
    try:
        # 設定 120 秒超時，考慮到本地模型執行較慢
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        print(f"🤖 助理回應: {data['reply']}")
        if data.get("tools_used"):
            print(f"🛠️ 使用工具: {', '.join(data['tools_used'])}")
        else:
            print("🛠️ 未使用任何外部工具。")
            
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    print("🚀 開始測試台北旅遊助手...")
    
    # 測試 1: 查詢捷運站座標 (TDX)
    test_chat("請問台北車站的座標在哪裡？")
    
    # 測試 2: 查詢附近美食 (OSM Amenities)
    test_chat("幫我找這附近的餐廳", lat=25.0173, lon=121.5397) # 座標為公館附近
    
    # 測試 3: 查詢歷史景點 (OSM History)
    test_chat("這附近有什麼古蹟嗎？", lat=25.0421, lon=121.5083) # 座標為西門町/中山堂附近
    
    # 測試 4: 一般閒聊 (不使用工具)
    test_chat("你好，你是誰？")

    test_chat("Hello,告訴我現在的新店捷運綠線車況")
