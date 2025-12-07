import csv
from datetime import datetime
from io import StringIO
from typing import Annotated
from pydantic import BaseModel, PlainSerializer


# 用 Annotated 讓 float 序列化時只保留 2 位小數
Float2 = Annotated[float, PlainSerializer(lambda x: round(x, 2), return_type=float)]


class SleepRecord(BaseModel):
    start: datetime
    end: datetime
    duration_hr: float
    value: str  # Core, REM, Deep, Awake


class SleepAnalysis(BaseModel):
    sleep_start: datetime
    sleep_end: datetime
    total_hours: Float2
    actual_sleep_hours: Float2  # 扣除 Awake
    deep_hours: Float2
    rem_hours: Float2
    core_hours: Float2
    awake_hours: Float2
    awake_count: int
    sleep_efficiency: Float2  # 實際睡眠 / 總時間
    quality_score: str  # 好 / 普通 / 差
    note: str


def parse_csv(csv_data: str) -> list[SleepRecord]:
    """解析 CSV 字串為 SleepRecord 列表。"""
    reader = csv.DictReader(StringIO(csv_data))
    return [
        SleepRecord(
            start=datetime.fromisoformat(row["Start"]),
            end=datetime.fromisoformat(row["End"]),
            duration_hr=float(row["Duration (hr)"]),
            value=row["Value"],
        )
        for row in reader
    ]


def analyze_sleep(csv_data: str) -> SleepAnalysis:
    """分析睡眠數據。"""
    records = parse_csv(csv_data)
    if not records:
        raise ValueError("沒有睡眠數據")

    # 計算各階段時數
    deep_hours = sum(r.duration_hr for r in records if r.value == "Deep")
    rem_hours = sum(r.duration_hr for r in records if r.value == "REM")
    core_hours = sum(r.duration_hr for r in records if r.value == "Core")
    awake_hours = sum(r.duration_hr for r in records if r.value == "Awake")
    awake_count = sum(1 for r in records if r.value == "Awake")

    total_hours = deep_hours + rem_hours + core_hours + awake_hours
    actual_sleep_hours = deep_hours + rem_hours + core_hours

    sleep_start = min(r.start for r in records)
    sleep_end = max(r.end for r in records)

    # 睡眠效率
    sleep_efficiency = actual_sleep_hours / total_hours if total_hours > 0 else 0

    # 品質評估
    # 好：深睡 > 1hr, REM > 1.5hr, 效率 > 85%, 總睡眠 > 7hr
    # 差：深睡 < 0.5hr 或 總睡眠 < 5hr 或 效率 < 75%
    if (
        deep_hours >= 1
        and rem_hours >= 1.5
        and sleep_efficiency >= 0.85
        and actual_sleep_hours >= 7
    ):
        quality_score = "好"
    elif deep_hours < 0.5 or actual_sleep_hours < 5 or sleep_efficiency < 0.75:
        quality_score = "差"
    else:
        quality_score = "普通"

    # 生成備註
    notes = []
    if sleep_start.hour >= 2:
        notes.append(f"凌晨 {sleep_start.hour}:{sleep_start.minute:02d} 才睡，太晚了")
    if actual_sleep_hours < 7:
        notes.append(f"只睡 {actual_sleep_hours:.1f} 小時，不足 7 小時")
    if deep_hours < 0.5:
        notes.append("深層睡眠不足")
    if awake_count > 5:
        notes.append(f"中途醒來 {awake_count} 次，睡眠品質差")

    note = "。".join(notes) if notes else "睡眠狀況正常"

    return SleepAnalysis(
        sleep_start=sleep_start,
        sleep_end=sleep_end,
        total_hours=round(total_hours, 2),
        actual_sleep_hours=round(actual_sleep_hours, 2),
        deep_hours=round(deep_hours, 2),
        rem_hours=round(rem_hours, 2),
        core_hours=round(core_hours, 2),
        awake_hours=round(awake_hours, 2),
        awake_count=awake_count,
        sleep_efficiency=round(sleep_efficiency, 2),
        quality_score=quality_score,
        note=note,
    )


if __name__ == "__main__":
    csv_data = """Start,End,Duration (hr),Value,Source
2025-12-04 03:17:09,2025-12-04 03:18:09,0.017,Core,Tsung-Hua的Apple Watch
2025-12-04 03:18:09,2025-12-04 03:19:40,0.025,Awake,Tsung-Hua的Apple Watch
2025-12-04 03:19:40,2025-12-04 03:26:40,0.117,Core,Tsung-Hua的Apple Watch
2025-12-04 03:26:40,2025-12-04 03:33:40,0.117,Awake,Tsung-Hua的Apple Watch
2025-12-04 03:33:40,2025-12-04 03:49:40,0.267,Core,Tsung-Hua的Apple Watch
2025-12-04 03:49:40,2025-12-04 03:51:40,0.033,Awake,Tsung-Hua的Apple Watch
2025-12-04 03:51:40,2025-12-04 04:03:41,0.2,Core,Tsung-Hua的Apple Watch
2025-12-04 04:03:41,2025-12-04 04:35:42,0.534,REM,Tsung-Hua的Apple Watch
2025-12-04 04:35:42,2025-12-04 04:46:42,0.183,Awake,Tsung-Hua的Apple Watch
2025-12-04 04:46:42,2025-12-04 05:06:12,0.325,Core,Tsung-Hua的Apple Watch
2025-12-04 05:06:12,2025-12-04 05:14:13,0.133,Awake,Tsung-Hua的Apple Watch
2025-12-04 05:14:13,2025-12-04 05:18:43,0.075,Core,Tsung-Hua的Apple Watch
2025-12-04 05:18:43,2025-12-04 05:20:43,0.033,Awake,Tsung-Hua的Apple Watch
2025-12-04 05:20:43,2025-12-04 05:22:13,0.025,Core,Tsung-Hua的Apple Watch
2025-12-04 05:22:13,2025-12-04 05:24:13,0.033,Awake,Tsung-Hua的Apple Watch
2025-12-04 05:24:13,2025-12-04 05:37:43,0.225,Core,Tsung-Hua的Apple Watch
2025-12-04 05:37:43,2025-12-04 06:05:44,0.467,Awake,Tsung-Hua的Apple Watch
2025-12-04 06:05:44,2025-12-04 06:27:14,0.358,Core,Tsung-Hua的Apple Watch
2025-12-04 06:27:14,2025-12-04 06:29:14,0.033,Awake,Tsung-Hua的Apple Watch
2025-12-04 06:29:14,2025-12-04 06:46:45,0.292,Core,Tsung-Hua的Apple Watch
2025-12-04 06:46:45,2025-12-04 06:55:45,0.15,Deep,Tsung-Hua的Apple Watch
2025-12-04 06:55:45,2025-12-04 07:14:16,0.308,Core,Tsung-Hua的Apple Watch
2025-12-04 07:14:16,2025-12-04 07:24:46,0.175,Deep,Tsung-Hua的Apple Watch
2025-12-04 07:24:46,2025-12-04 07:29:46,0.083,Core,Tsung-Hua的Apple Watch
2025-12-04 07:29:46,2025-12-04 07:30:46,0.017,Awake,Tsung-Hua的Apple Watch
2025-12-04 07:30:46,2025-12-04 07:33:46,0.05,Core,Tsung-Hua的Apple Watch
2025-12-04 07:33:46,2025-12-04 08:22:17,0.809,REM,Tsung-Hua的Apple Watch
2025-12-04 08:22:17,2025-12-04 08:39:18,0.283,Core,Tsung-Hua的Apple Watch
2025-12-04 08:39:18,2025-12-04 08:42:18,0.05,Deep,Tsung-Hua的Apple Watch
2025-12-04 08:42:18,2025-12-04 08:54:48,0.208,Core,Tsung-Hua的Apple Watch
2025-12-04 08:54:48,2025-12-04 08:55:48,0.017,Awake,Tsung-Hua的Apple Watch
2025-12-04 08:55:48,2025-12-04 09:18:49,0.383,Core,Tsung-Hua的Apple Watch
2025-12-04 09:18:49,2025-12-04 09:40:19,0.358,Deep,Tsung-Hua的Apple Watch
2025-12-04 09:40:19,2025-12-04 09:45:49,0.092,Awake,Tsung-Hua的Apple Watch
2025-12-04 09:45:49,2025-12-04 09:56:50,0.183,Core,Tsung-Hua的Apple Watch
2025-12-04 09:56:50,2025-12-04 10:00:20,0.058,REM,Tsung-Hua的Apple Watch
2025-12-04 10:00:20,2025-12-04 10:42:21,0.7,Core,Tsung-Hua的Apple Watch
2025-12-04 10:42:21,2025-12-04 10:45:51,0.058,Deep,Tsung-Hua的Apple Watch
2025-12-04 10:45:51,2025-12-04 10:46:51,0.017,Core,Tsung-Hua的Apple Watch
2025-12-04 10:46:51,2025-12-04 10:49:51,0.05,Awake,Tsung-Hua的Apple Watch
2025-12-04 10:49:51,2025-12-04 10:51:21,0.025,Core,Tsung-Hua的Apple Watch
2025-12-04 10:51:21,2025-12-04 11:00:21,0.15,REM,Tsung-Hua的Apple Watch
2025-12-04 11:00:21,2025-12-04 11:01:51,0.025,Awake,Tsung-Hua的Apple Watch
2025-12-04 11:01:51,2025-12-04 11:48:23,0.775,REM,Tsung-Hua的Apple Watch
2025-12-04 11:48:23,2025-12-04 11:55:23,0.117,Awake,Tsung-Hua的Apple Watch
2025-12-04 11:55:23,2025-12-04 12:02:23,0.117,Core,Tsung-Hua的Apple Watch
2025-12-04 12:02:23,2025-12-04 12:05:23,0.05,REM,Tsung-Hua的Apple Watch"""

    result = analyze_sleep(csv_data)
    print(f"睡眠時間：{result.sleep_start} ~ {result.sleep_end}")
    print(f"總時數：{result.total_hours} 小時")
    print(f"實際睡眠：{result.actual_sleep_hours} 小時")
    print(f"深層：{result.deep_hours}hr / REM：{result.rem_hours}hr / 淺層：{result.core_hours}hr")
    print(f"醒來：{result.awake_count} 次（共 {result.awake_hours}hr）")
    print(f"睡眠效率：{result.sleep_efficiency * 100:.0f}%")
    print(f"品質：{result.quality_score}")
    print(f"備註：{result.note}")
