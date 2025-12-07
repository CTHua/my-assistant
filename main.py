from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel

from todoist_service import get_tasks
from sleep_service import analyze_sleep
from gemini_service import generate_morning_message
from weather_service import get_weather
from calendar_service import get_today_events, format_events_for_prompt

app = FastAPI(title="Personal AI Assistant")


class MorningRequest(BaseModel):
    sleep_csv: str  # Apple Watch 睡眠數據 CSV
    location: str = "新竹市"  # 天氣查詢地點


class MorningResponse(BaseModel):
    summary: str  # Gemini 總結
    todos: list[str]  # 待辦清單
    weather: str  # 天氣摘要
    events: list[dict]  # 今日行程
    display: str  # 給捷徑顯示用的完整文字


@app.get("/health")
async def health_check():
    """健康檢查。"""
    return {"status": "ok"}


@app.post("/morning")
async def morning(request: MorningRequest):
    """早安流程。"""
    # 分析睡眠
    sleep = analyze_sleep(request.sleep_csv)

    # 取得天氣
    weather = await get_weather(request.location)
    weather_summary = weather.get("summary", "天氣資料取得失敗")

    # 取得今日行程
    events = get_today_events()
    events_text = format_events_for_prompt(events)

    # 取得待辦事項
    tasks = get_tasks()
    todo_list = [t.content for t in tasks[:5]]

    # Gemini 生成個人化訊息
    sleep_time = sleep.sleep_start.strftime("%H:%M")
    wake_time = sleep.sleep_end.strftime("%H:%M")
    summary = await generate_morning_message(
        sleep_time=sleep_time,
        wake_time=wake_time,
        sleep_hours=sleep.actual_sleep_hours,
        quality=sleep.quality_score,
        todos=todo_list,
        weather=weather_summary,
        events=events_text,
    )

    # 組合顯示文字
    todo_text = "\n".join(f"• {t}" for t in todo_list) if todo_list else "無待辦"
    events_display = "\n".join(f"• {e['start']} {e['summary']}" for e in events) if events else "無行程"
    display = f"🌤 {weather_summary}\n\n{summary}\n\n📅 行程：\n{events_display}\n\n📋 待辦：\n{todo_text}"

    return MorningResponse(
        summary=summary,
        todos=todo_list,
        weather=weather_summary,
        events=events,
        display=display,
    )


@app.get("/test/morning")
async def test_morning():
    """測試早安流程（使用假睡眠數據）。"""
    # 假睡眠數據
    sleep_csv = """Start,End,Duration (hr),Value,Source
2025-12-04 03:17:09,2025-12-04 03:18:09,0.017,Core,Test
2025-12-04 03:18:09,2025-12-04 03:19:40,0.025,Awake,Test
2025-12-04 03:19:40,2025-12-04 10:00:00,6.67,Core,Test
2025-12-04 10:00:00,2025-12-04 11:00:00,1.0,REM,Test
2025-12-04 11:00:00,2025-12-04 12:05:23,1.09,Deep,Test"""

    sleep = analyze_sleep(sleep_csv)

    # 取得天氣
    weather = await get_weather("新竹市")
    weather_summary = weather.get("summary", "天氣資料取得失敗")

    # 取得今日行程
    events = get_today_events()
    events_text = format_events_for_prompt(events)

    tasks = get_tasks()
    todo_list = [t.content for t in tasks[:5]]

    sleep_time = sleep.sleep_start.strftime("%H:%M")
    wake_time = sleep.sleep_end.strftime("%H:%M")
    summary = await generate_morning_message(
        sleep_time=sleep_time,
        wake_time=wake_time,
        sleep_hours=sleep.actual_sleep_hours,
        quality=sleep.quality_score,
        todos=todo_list,
        weather=weather_summary,
        events=events_text,
    )

    todo_text = "\n".join(f"• {t}" for t in todo_list) if todo_list else "無待辦"
    events_display = "\n".join(f"• {e['start']} {e['summary']}" for e in events) if events else "無行程"
    display = f"🌤 {weather_summary}\n\n{summary}\n\n📅 行程：\n{events_display}\n\n📋 待辦：\n{todo_text}"

    return MorningResponse(
        summary=summary,
        todos=todo_list,
        weather=weather_summary,
        events=events,
        display=display,
    )


@app.get("/test/tasks")
async def test_tasks():
    """測試取得 Todoist 待辦事項。"""
    tasks = get_tasks()
    return {
        "count": len(tasks),
        "tasks": [{"id": t.id, "content": t.content} for t in tasks],
    }


class SleepAnalysisRequest(BaseModel):
    csv_data: str


@app.post("/analyze/sleep")
async def analyze_sleep_endpoint(request: SleepAnalysisRequest):
    """分析睡眠數據（接收 CSV 格式）。"""
    return analyze_sleep(request.csv_data)
