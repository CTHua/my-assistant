import os
from dotenv import load_dotenv
import httpx

load_dotenv()

CWA_API_KEY = os.getenv("CWA_API_KEY")
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"


async def get_weather(location: str = "新竹縣") -> dict:
    """取得天氣預報。

    Args:
        location: 縣市名稱，例如 "新竹縣"、"新竹市"、"台北市"

    Returns:
        天氣資訊 dict
    """
    # F-C0032-001: 一般天氣預報-今明 36 小時天氣預報
    url = f"{BASE_URL}/F-C0032-001"
    params = {
        "Authorization": CWA_API_KEY,
        "locationName": location,
    }

    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

    records = data.get("records", {})
    locations = records.get("location", [])

    if not locations:
        return {"error": f"找不到 {location} 的天氣資料"}

    loc = locations[0]
    weather_elements = {e["elementName"]: e for e in loc["weatherElement"]}

    # 取得各項天氣資訊（取第一個時段）
    wx = weather_elements.get("Wx", {}).get("time", [{}])[0]  # 天氣現象
    pop = weather_elements.get("PoP", {}).get("time", [{}])[0]  # 降雨機率
    min_t = weather_elements.get("MinT", {}).get("time", [{}])[0]  # 最低溫
    max_t = weather_elements.get("MaxT", {}).get("time", [{}])[0]  # 最高溫
    ci = weather_elements.get("CI", {}).get("time", [{}])[0]  # 舒適度

    return {
        "location": location,
        "description": wx.get("parameter", {}).get("parameterName", ""),
        "rain_probability": pop.get("parameter", {}).get("parameterName", ""),
        "min_temp": min_t.get("parameter", {}).get("parameterName", ""),
        "max_temp": max_t.get("parameter", {}).get("parameterName", ""),
        "comfort": ci.get("parameter", {}).get("parameterName", ""),
        "summary": f"{wx.get('parameter', {}).get('parameterName', '')}，{min_t.get('parameter', {}).get('parameterName', '')}~{max_t.get('parameter', {}).get('parameterName', '')}°C，降雨機率 {pop.get('parameter', {}).get('parameterName', '')}%",
    }


if __name__ == "__main__":
    import asyncio

    async def main():
        weather = await get_weather("新竹市")
        print(f"地點: {weather.get('location')}")
        print(f"天氣: {weather.get('description')}")
        print(f"溫度: {weather.get('min_temp')}~{weather.get('max_temp')}°C")
        print(f"降雨機率: {weather.get('rain_probability')}%")
        print(f"舒適度: {weather.get('comfort')}")
        print(f"總結: {weather.get('summary')}")

    asyncio.run(main())
