from datetime import datetime, date
from fastapi import FastAPI
from pydantic import BaseModel

from todoist_service import get_tasks
from sleep_service import analyze_sleep
from gemini_service import generate_morning_message
from weather_service import get_weather
from calendar_service import get_today_events, format_events_for_prompt
from db_service import save_sleep_record, get_recent_sleep_records, get_morning_cache, save_morning_cache

app = FastAPI(title="Personal AI Assistant")


def format_display(
    summary: str,
    weather: str,
    events: list[dict],
    todos: list[str],
) -> str:
    """格式化顯示文字，適合 iOS 捷徑顯示。"""
    lines = []
    divider = " " * 20

    # 天氣區塊
    lines.append(f"☀️ 天氣｜{weather}")
    lines.append("")

    # AI 摘要
    lines.append(summary)
    lines.append("")
    lines.append(divider)

    # 行程區塊
    lines.append("📅 今日行程")
    if events:
        for e in events:
            loc = f" @ {e['location']}" if e.get("location") else ""
            lines.append(f"  {e['start']}  {e['summary']}{loc}")
    else:
        lines.append("  無行程")
    lines.append("")
    lines.append(divider)

    # 待辦區塊
    lines.append("📋 待辦事項")
    if todos:
        for i, t in enumerate(todos, 1):
            lines.append(f"  {i}. {t}")
    else:
        lines.append("  無待辦")

    return "\n".join(lines)


class MorningRequest(BaseModel):
    sleep_csv: str  # Apple Watch 睡眠數據 CSV
    location: str = "新竹市"  # 天氣查詢地點


class MorningResponse(BaseModel):
    summary: str  # Gemini 總結
    todos: list[str]  # 待辦清單
    weather: str  # 天氣摘要
    events: list[dict]  # 今日行程
    display: str  # 給捷徑顯示用的完整文字
    cached: bool = False  # 是否來自快取


@app.get("/health")
async def health_check():
    """健康檢查。"""
    return {"status": "ok"}


@app.post("/morning")
async def morning(request: MorningRequest):
    """早安流程。"""
    today = date.today()

    cached = get_morning_cache(today)
    if cached:
        return MorningResponse(
            summary=cached["summary"],
            todos=cached["todos"],
            weather=cached["weather"],
            events=cached["events"],
            display=cached["display"],
            cached=True,
        )

    sleep = analyze_sleep(request.sleep_csv)

    weather = await get_weather(request.location)
    weather_summary = weather.get("summary", "天氣資料取得失敗")

    events = get_today_events()
    events_text = format_events_for_prompt(events)

    tasks = get_tasks()
    todo_list = [t.content for t in tasks[:5]]

    sleep_time = sleep.sleep_start.strftime("%H:%M")
    wake_time = sleep.sleep_end.strftime("%H:%M")

    save_sleep_record(
        sleep_date=sleep.sleep_end.date(),
        sleep_start=sleep.sleep_start,
        sleep_end=sleep.sleep_end,
        total_hours=sleep.total_hours,
        actual_sleep_hours=sleep.actual_sleep_hours,
        deep_hours=sleep.deep_hours,
        rem_hours=sleep.rem_hours,
        core_hours=sleep.core_hours,
        awake_hours=sleep.awake_hours,
        awake_count=sleep.awake_count,
        sleep_efficiency=sleep.sleep_efficiency,
        quality_score=sleep.quality_score,
        note=sleep.note,
    )

    try:
        summary = await generate_morning_message(
            sleep_time=sleep_time,
            wake_time=wake_time,
            sleep_hours=sleep.actual_sleep_hours,
            quality=sleep.quality_score,
            todos=todo_list,
            weather=weather_summary,
            events=events_text,
        )
    except Exception as e:
        summary = f"生成早安訊息時發生錯誤：{str(e)}"

    display = format_display(summary, weather_summary, events, todo_list)

    save_morning_cache(
        cache_date=today,
        summary=summary,
        weather=weather_summary,
        events=events,
        todos=todo_list,
        display=display,
    )

    return MorningResponse(
        summary=summary,
        todos=todo_list,
        weather=weather_summary,
        events=events,
        display=display,
        cached=False,
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
    
    summary = "測試用ai回覆，有天氣、行程、待辦事項"

    display = format_display(summary, weather_summary, events, todo_list)

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


@app.post("/test/sleep_analyze")
async def analyze_sleep_endpoint(request: SleepAnalysisRequest):
    """分析睡眠數據（接收 CSV 格式）。"""
    return analyze_sleep(request.csv_data)


@app.get("/sleep/history")
async def get_sleep_history(days: int = 7):
    """取得最近 N 天的睡眠紀錄。"""
    return get_recent_sleep_records(days)
