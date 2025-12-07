import os
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)  # 強制重新載入 .env

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
client = genai.Client(api_key=GEMINI_API_KEY)

PERSONAL_CONTEXT = """
你是我的個人助理，負責每天早上給我簡短的 briefing。

【我的基本資訊】
- 住在新竹
- 作息目標：02:00 前睡，睡滿 7 小時
- 有同居伴侶

【回應風格】
- 簡短、實用、不囉唆
- 先講天氣，再講行程，最後講睡眠
- 只在睡眠數據明顯有問題時才提（例如睡不到 5 小時、凌晨 4 點後才睡）
- 繁體中文
- 不要用 emoji
- 不要說「早安」或打招呼
"""


async def generate_morning_message(
    sleep_time: str,
    wake_time: str,
    sleep_hours: float,
    quality: str,
    todos: list[str],
    weather: str = "",
    events: str = "",
) -> str:
    """生成早安訊息。"""
    todo_text = "\n".join(f"- {t}" for t in todos[:5]) if todos else "無待辦"

    prompt = f"""{PERSONAL_CONTEXT}

【今日天氣】
{weather}

【今日行程】
{events if events else "今日無行程"}

【今日睡眠】
- 入睡：{sleep_time}
- 起床：{wake_time}
- 實際睡眠：{sleep_hours:.1f} 小時
- 品質：{quality}

【待辦事項】
{todo_text}

根據以上資訊，給我一段早安提醒（50 字內），重點放在：
1. 天氣提醒（需要帶傘、注意溫差等）
2. 今日行程提醒（有重要會議或活動時提）
3. 睡眠狀況評價（只在明顯有問題時提）
4. 今天最該優先處理的事
"""

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    if response.text:
        return response.text.strip()
    return f"{sleep_time} 睡、{wake_time} 起，睡 {sleep_hours:.1f}hr，品質{quality}"


if __name__ == "__main__":
    import asyncio

    async def main():
        msg = await generate_morning_message(
            sleep_time="03:17",
            wake_time="12:05",
            sleep_hours=7.4,
            quality="普通",
            todos=["看能不能當天預約除毛", "訂機票"],
        )
        print("Message:", msg)

    asyncio.run(main())
