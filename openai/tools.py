import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# 全域設定 & 憑證
# ==========================================
# OSM 設定
USER_AGENT = os.getenv("USER_AGENT", "TaipeiTravelAssistant/1.0")
OSM_OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# TDX 設定
TDX_CLIENT_ID = os.getenv("TDX_CLIENT_ID")
TDX_CLIENT_SECRET = os.getenv("TDX_CLIENT_SECRET")
TDX_AUTH_URL = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
BASE_TDX_URL = "https://tdx.transportdata.tw"

# ==========================================
# TDX 快取記憶體
# ==========================================
tdx_token_cache = {
    "access_token": None,
    "expires_at": 0
}

# ==========================================
# 工具 1：TDX API 核心與驗證
# ==========================================
def get_valid_tdx_token():
    """取得 TDX Token，並實作快取與過期檢查機制"""
    global tdx_token_cache
    current_time = time.time()
    
    if tdx_token_cache["access_token"] and current_time < (tdx_token_cache["expires_at"] - 60):
        return tdx_token_cache["access_token"]

    data = {
        "grant_type": "client_credentials",
        "client_id": TDX_CLIENT_ID,
        "client_secret": TDX_CLIENT_SECRET
    }
    try:
        response = requests.post(TDX_AUTH_URL, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        tdx_token_cache["access_token"] = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 86400) 
        tdx_token_cache["expires_at"] = current_time + expires_in
        
        return tdx_token_cache["access_token"]
    except Exception as e:
        print(f"TDX 驗證失敗: {e}")
        return None

def fetch_mrt_station_info(station_name: str):
    """
    抓取台北捷運站基本資料。
    
    Args:
        station_name: 捷運站名稱 (例如: "台北車站", "公館")
    """
    token = get_valid_tdx_token()
    if not token:
        return "無法取得 TDX 捷運資料 (未授權)"
        
    url = f"{BASE_TDX_URL}/api/basic/v2/Rail/Metro/Station/TRTC"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Encoding": "gzip"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        stations = response.json()
        
        for s in stations:
            if station_name in s.get("StationName", {}).get("Zh_tw", ""):
                lat = s['StationPosition']['PositionLat']
                lon = s['StationPosition']['PositionLon']
                return f"車站資訊：{s['StationName']['Zh_tw']}，座標 ({lat}, {lon})"
        return f"找不到名為 {station_name} 的車站"
    except Exception as e:
        status = getattr(e.response, 'status_code', 'Unknown')
        return f"TDX 資料抓取失敗: {e} (HTTP 狀態碼: {status})"

# ==========================================
# 工具 2：OSM 設施與美食串接
# ==========================================
def fetch_osm_amenities(lat: float, lon: float, amenity_type: str = "restaurant", radius: int = 500):
    """
    搜尋指定座標附近的特定設施 (例如：美食、咖啡廳)。
    
    Args:
        lat: 緯度
        lon: 經度
        amenity_type: 設施類型 (例如: "restaurant", "cafe", "bar", "fast_food")
        radius: 搜尋半徑 (公尺)，預設 500
    """
    overpass_query = f"""
    [out:json][timeout:10];
    node["amenity"="{amenity_type}"](around:{radius},{lat},{lon});
    out tags 5;
    """
    headers = {
        'Content-Type': 'text/plain',
        'User-Agent': USER_AGENT
    }
    try:
        response = requests.post(OSM_OVERPASS_URL, headers=headers, data=overpass_query.encode('utf-8'))
        response.raise_for_status()
        osm_data = response.json()
        
        simplified_results = []
        for element in osm_data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name')
            if name: 
                simplified_results.append(f"- 【{name}】")
        
        if simplified_results:
            return f"OSM 附近 {amenity_type} 推薦：\n" + "\n".join(simplified_results)
        return f"OSM 附近 {radius} 公尺內無具名的 {amenity_type}。"
    except Exception as e:
        return f"OSM 美食查詢失敗: {e}"

# ==========================================
# 工具 3：OSM 歷史古蹟串接
# ==========================================
def fetch_osm_historical_spots(lat: float, lon: float, radius: int = 1000):
    """
    透過 OSM 尋找座標附近有明確名稱的歷史景點與古蹟。
    
    Args:
        lat: 緯度
        lon: 經度
        radius: 搜尋半徑 (公尺)，預設 1000
    """
    overpass_query = f"""
    [out:json][timeout:10];
    nwr["historic"]["name"](around:{radius},{lat},{lon});
    out tags top 3;
    """
    headers = {
        'Content-Type': 'text/plain',
        'User-Agent': USER_AGENT
    }
    try:
        response = requests.post(OSM_OVERPASS_URL, headers=headers, data=overpass_query.encode('utf-8'))
        response.raise_for_status()
        data = response.json()
        
        spots = []
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name")
            historic_type = tags.get("historic", "未知類別")
            if name: 
                spots.append(f"- 【{name}】 (類別: {historic_type})")
        
        if spots:
            return "OSM 附近歷史景點：\n" + "\n".join(spots)
        return f"OSM 附近 {radius} 公尺內無具名歷史景點。"
    except Exception as e:
        return f"OSM 古蹟查詢失敗: {e}"

# ==========================================
# 工具定義 (用於 OpenAI Function Calling)
# ==========================================
TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "fetch_mrt_station_info",
            "description": "抓取台北捷運站基本資料與座標。",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_name": {"type": "string", "description": "捷運站名稱 (例如: '台北車站', '公館')"}
                },
                "required": ["station_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_osm_amenities",
            "description": "搜尋指定座標附近的特定設施 (例如：美食、咖啡廳)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "緯度"},
                    "lon": {"type": "number", "description": "經度"},
                    "amenity_type": {"type": "string", "description": "設施類型 (例如: 'restaurant', 'cafe', 'bar', 'fast_food')"},
                    "radius": {"type": "integer", "description": "搜尋半徑 (公尺)"}
                },
                "required": ["lat", "lon"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_osm_historical_spots",
            "description": "透過 OSM 尋找座標附近有明確名稱的歷史景點與古蹟。",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "緯度"},
                    "lon": {"type": "number", "description": "經度"},
                    "radius": {"type": "integer", "description": "搜尋半徑 (公尺)"}
                },
                "required": ["lat", "lon"]
            }
        }
    }
]

# 工具映射
AVAILABLE_FUNCTIONS = {
    "fetch_mrt_station_info": fetch_mrt_station_info,
    "fetch_osm_amenities": fetch_osm_amenities,
    "fetch_osm_historical_spots": fetch_osm_historical_spots
}